"""P4.6 effect boundary. Import is inert; implementation approval is never execution authority.

Low-level primitives are also exercised with tiny temporary unit fixtures. Only
ExecutionSession connects them to real product bundles and external authorization.
Linux, local filesystem and a trusted same-UID operator are explicit requirements.
"""
from __future__ import annotations
import contextlib
import ctypes
import errno
import fcntl
import os
from pathlib import Path
import stat
import time

from .business_execution_contracts import (
    ROOT, ContractError, canonical, contract, digest, loads, object_hash, path_set,
    relative_path, require,
)
from .business_execution_authority import authorization_context
from .business_generation import CODE_PATHS, tree_hash, validate_bundle

B_FILES = ('factory/business_materialization.py', 'scripts/validate_business_generation.py',
           'scripts/check_business_generation_browser.mjs', 'tests/test_business_materialization.py')
NOFOLLOW = os.O_NOFOLLOW | os.O_CLOEXEC
DIRECTORY = NOFOLLOW | os.O_DIRECTORY | os.O_RDONLY
MAX_FILE = 32 * 1024 * 1024


def identity(info):
    return (info.st_dev, info.st_ino)


def absolute(path):
    value = str(path)
    require(value.startswith('/') and str(Path(value)) == value and value != '/', 'canonical absolute path required')
    relative_path(value[1:])
    return Path(value)


def open_directory(path):
    """Walk from / using directory descriptors: no symlink ancestor can be followed."""
    path = absolute(path)
    fd = os.open('/', DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, DIRECTORY, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def regular(fd, maximum=MAX_FILE):
    info = os.fstat(fd)
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid(),
            'non-regular, linked or foreign file')
    require(info.st_size <= maximum, 'file budget exceeded')
    return info


def read_fd(fd, maximum=MAX_FILE):
    before = regular(fd, maximum)
    os.lseek(fd, 0, os.SEEK_SET)
    chunks = []
    size = 0
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        size += len(chunk)
        require(size <= maximum, 'read budget exceeded')
        chunks.append(chunk)
    after = regular(fd, maximum)
    require((identity(before), before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (identity(after), after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'file changed while reading')
    return b''.join(chunks)


def secure_read(path):
    path = absolute(path)
    parent = open_directory(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | NOFOLLOW, dir_fd=parent)
        try:
            raw = read_fd(fd)
            require(identity(os.stat(path.name, dir_fd=parent, follow_symlinks=False)) == identity(os.fstat(fd)),
                    'file replaced while reading')
            return raw
        finally:
            os.close(fd)
    finally:
        os.close(parent)


class Directory:
    """Pinned existing directory. Never creates a workspace implicitly."""
    def __init__(self, path, *, private=False):
        self.path = absolute(path)
        self.fd = open_directory(self.path)
        self.inode = identity(os.fstat(self.fd))
        if private:
            info = os.fstat(self.fd)
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                self.close()
                raise ContractError('control/owned directory must be private 0700')

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def check(self):
        require(self.fd is not None, 'closed directory')
        fresh = open_directory(self.path)
        try:
            require(identity(os.fstat(fresh)) == self.inode == identity(os.fstat(self.fd)), 'directory identity changed')
        finally:
            os.close(fresh)

    def read(self, name, maximum=MAX_FILE):
        relative_path(name)
        require('/' not in name, 'single filename required')
        self.check()
        fd = os.open(name, os.O_RDONLY | NOFOLLOW, dir_fd=self.fd)
        try:
            raw = read_fd(fd, maximum)
            require(identity(os.stat(name, dir_fd=self.fd, follow_symlinks=False)) == identity(os.fstat(fd)), 'file swapped')
            self.check()
            return raw
        finally:
            os.close(fd)

    def create(self, name, raw, guard):
        relative_path(name)
        require('/' not in name and type(raw) is bytes and len(raw) <= MAX_FILE, 'invalid creation')
        guard()
        self.check()
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | NOFOLLOW, 0o600, dir_fd=self.fd)
        try:
            regular(fd)
            view = memoryview(raw)
            while view:
                count = os.write(fd, view)
                require(count > 0, 'short write')
                view = view[count:]
            os.fsync(fd)
            result = identity(os.fstat(fd))
        finally:
            os.close(fd)
        os.fsync(self.fd)
        self.check()
        return result


class Journal:
    """Append-only hash chain. Caller holds the operation lock; corrupt tails fail closed."""
    def __init__(self, directory, name='journal.jsonl'):
        self.directory = directory
        relative_path(name)
        require('/' not in name, 'journal filename')
        self.name = name

    def read(self):
        try:
            raw = self.directory.read(self.name)
        except FileNotFoundError:
            return []
        require(not raw or raw.endswith(b'\n'), 'torn journal tail; manual recovery required')
        result, previous = [], 'sha256:' + '0'*64
        for line in raw.splitlines():
            row = loads(line)
            require(type(row) is dict and set(row) == {'sequence','previous','event','hash'}, 'invalid journal record')
            body = {k:row[k] for k in ('sequence','previous','event')}
            require(row['sequence'] == len(result) and row['previous'] == previous and
                    row['hash'] == object_hash(body), 'journal integrity failure')
            result.append(row)
            previous = row['hash']
        return result

    def append(self, event, guard):
        require(type(event) is dict and type(event.get('kind')) is str, 'journal event required')
        guard()
        rows = self.read()
        body = {'sequence':len(rows),'previous':rows[-1]['hash'] if rows else 'sha256:'+'0'*64,'event':event}
        raw = canonical({**body,'hash':object_hash(body)})
        self.directory.check()
        fd = os.open(self.name, os.O_WRONLY | os.O_APPEND | os.O_CREAT | NOFOLLOW, 0o600,
                     dir_fd=self.directory.fd)
        try:
            regular(fd)
            require(os.fstat(fd).st_size + len(raw) <= MAX_FILE, 'journal budget exceeded')
            require(os.write(fd,raw) == len(raw), 'torn journal write')
            os.fsync(fd)
        finally:
            os.close(fd)
        os.fsync(self.directory.fd)
        self.directory.check()


class UseRegistry:
    """flock + exclusive durable claim; a crashed or failed claim is never recycled."""
    def __init__(self, control):
        self.control = control
        self.journal = Journal(control)

    @contextlib.contextmanager
    def lock(self, guard):
        guard()
        self.control.check()
        fd = os.open('operation.lock', os.O_RDWR | os.O_CREAT | NOFOLLOW, 0o600, dir_fd=self.control.fd)
        try:
            regular(fd)
            fcntl.flock(fd, fcntl.LOCK_EX)
            self.control.check()
            require(identity(os.stat('operation.lock',dir_fd=self.control.fd,follow_symlinks=False)) == identity(os.fstat(fd)),
                    'lock replaced')
            self.journal.read()
            guard()
            yield
        finally:
            fcntl.flock(fd,fcntl.LOCK_UN)
            os.close(fd)

    @contextlib.contextmanager
    def reserve(self, run_id, action, binding, guard):
        require(type(run_id) is str and type(action) is str and run_id and action, 'use identity missing')
        key = object_hash({'runId':run_id,'action':action}).split(':')[1]
        with self.lock(guard):
            # O_EXCL is the durable linearization point even across process interruption.
            self.control.create('use-'+key+'.json',canonical({'runId':run_id,'action':action,'binding':binding}),guard)
            self.journal.append({'kind':'use-reserved','runId':run_id,'action':action,'binding':binding},guard)
            try:
                guard()
                yield self.journal
            except BaseException:
                # A stale permit cannot authorize another write. The durable claim itself
                # already proves non-reusability if recording the failure is no longer allowed.
                raise
            else:
                self.journal.append({'kind':'use-completed','runId':run_id,'action':action,'binding':binding},guard)

    @contextlib.contextmanager
    def reserve_many(self, run_id, actions, binding, guard):
        require(actions and len(set(actions)) == len(actions), 'unique actions required')
        with self.lock(guard):
            for action in actions:
                key = object_hash({'runId':run_id,'action':action}).split(':')[1]
                self.control.create('use-'+key+'.json',canonical({'runId':run_id,'action':action,'binding':binding}),guard)
                self.journal.append({'kind':'use-reserved','runId':run_id,'action':action,'binding':binding},guard)
            guard()
            yield self.journal
            for action in actions:
                self.journal.append({'kind':'use-completed','runId':run_id,'action':action,'binding':binding},guard)


def rename_noreplace(source, name, destination, new_name, guard):
    """Linux renameat2(RENAME_NOREPLACE), with no check-then-rename fallback."""
    for value in (name,new_name):
        relative_path(value)
        require('/' not in value, 'rename basename required')
    guard()
    source.check()
    destination.check()
    require(os.fstat(source.fd).st_dev == os.fstat(destination.fd).st_dev, 'cross-filesystem promotion forbidden')
    try:
        operation = ctypes.CDLL(None,use_errno=True).renameat2
    except AttributeError as exc:
        raise ContractError('atomic no-replace unavailable') from exc
    operation.argtypes = [ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
    operation.restype = ctypes.c_int
    if operation(source.fd,os.fsencode(name),destination.fd,os.fsencode(new_name),1):
        code = ctypes.get_errno()
        raise OSError(code,os.strerror(code))
    os.fsync(source.fd)
    os.fsync(destination.fd)
    source.check()
    destination.check()


def snapshot(path, *, build_links=False):
    """Full tree, including directory inode ownership; refuses links and special files."""
    result = {}
    with Directory(path,private=True) as root:
        def visit(fd, prefix):
            for name in sorted(os.listdir(fd)):
                relative_path(name)
                info = os.stat(name,dir_fd=fd,follow_symlinks=False)
                key = prefix+name
                require(info.st_uid == os.getuid(), 'foreign tree entry')
                if stat.S_ISLNK(info.st_mode):
                    require(build_links and key.startswith('node_modules/'), 'source symlink forbidden')
                    link = os.readlink(name,dir_fd=fd)
                    target = (Path(path)/key).resolve(strict=True)
                    require(not os.path.isabs(link) and target.is_relative_to(Path(path)/'node_modules'), 'derived link escape')
                    require(identity(os.stat(name,dir_fd=fd,follow_symlinks=False)) == identity(info), 'derived link changed')
                    result[key] = {'kind':'build-link','inode':list(identity(info)),'target':link}
                elif stat.S_ISDIR(info.st_mode):
                    child = os.open(name,DIRECTORY,dir_fd=fd)
                    try:
                        require(identity(os.fstat(child)) == identity(info), 'directory race')
                        result[key] = {'kind':'directory','inode':list(identity(info))}
                        visit(child,key+'/')
                    finally:
                        os.close(child)
                else:
                    child = os.open(name,os.O_RDONLY | NOFOLLOW | os.O_NONBLOCK,dir_fd=fd)
                    try:
                        require(identity(os.fstat(child)) == identity(info), 'entry race')
                        result[key] = {'kind':'file','inode':list(identity(info)),'sha256':digest(read_fd(child,256*1024*1024 if build_links and key.startswith(('node_modules/','.next/')) else MAX_FILE))}
                    finally:
                        os.close(child)
            root.check()
        visit(root.fd,'')
        return {'rootInode':list(root.inode),'entries':result}


class OwnedTree:
    """Unit-tested small-files primitive; production use must come through ExecutionSession."""
    def __init__(self, path, journal, binding):
        self.path = absolute(path)
        self.journal = journal
        self.binding = binding

    def owned_snapshot(self):
        rows = [r['event'] for r in self.journal.read() if r['event'].get('path') == str(self.path)
                and r['event']['kind'] in ('tree-state','tree-promoted','tree-cleaned')]
        require(rows, 'no ownership receipt')
        latest = rows[-1]
        require(latest.get('binding') == self.binding and latest['kind'] in ('tree-state','tree-promoted'), 'ownership mismatch')
        return latest['snapshot']

    def verify(self):
        expected = self.owned_snapshot()
        actual = snapshot(self.path,build_links=any(x['kind']=='build-link' for x in expected['entries'].values()))
        require(actual == expected, 'owned tree modified/foreign content; no destructive cleanup')
        return actual

    def _record(self, guard, additions=None, *, initial=False):
        actual = snapshot(self.path)
        expected = {} if initial else dict(self.owned_snapshot()['entries'])
        for path,value in (additions or {}).items():
            require(path not in expected, 'state update would adopt an existing entry')
            expected[path] = value
        require(actual['entries'] == expected, 'unattributed entry appeared; ownership not adopted')
        self.journal.append({'kind':'tree-state','path':str(self.path),'binding':self.binding,
                             'snapshot':actual},guard)

    def create(self, files, guard):
        path_set(files)
        require(files and all(type(v) is bytes and len(v) <= MAX_FILE for v in files.values()), 'invalid payload')
        self.journal.append({'kind':'tree-create-intent','path':str(self.path),'binding':self.binding},guard)
        with Directory(self.path.parent) as parent:
            guard()
            parent.check()
            os.mkdir(self.path.name,0o700,dir_fd=parent.fd)  # no exist_ok
            os.fsync(parent.fd)
        self._record(guard,initial=True)
        for rel,raw in sorted(files.items()):
            self.verify()
            pieces = rel.split('/')
            current = self.path
            for piece in pieces[:-1]:
                child = current/piece
                with Directory(current,private=True) as directory:
                    if not child.exists():
                        self.journal.append({'kind':'mkdir-intent','path':str(child),'binding':self.binding},guard)
                        guard()
                        directory.check()
                        os.mkdir(piece,0o700,dir_fd=directory.fd)
                        os.fsync(directory.fd)
                        info = os.stat(piece,dir_fd=directory.fd,follow_symlinks=False)
                        self._record(guard,{str(child.relative_to(self.path)):{'kind':'directory','inode':list(identity(info))}})
                current = child
            self.journal.append({'kind':'file-create-intent','path':str(self.path),'relative':rel,'sha256':digest(raw),
                                 'binding':self.binding},guard)
            with Directory(current,private=True) as directory:
                inode = directory.create(pieces[-1],raw,guard)
            self._record(guard,{rel:{'kind':'file','inode':list(inode),'sha256':digest(raw)}})
        self.verify()
        return self.owned_snapshot()

    def promote(self, target, guard):
        target = absolute(target)
        before = self.verify()
        self.journal.append({'kind':'promote-intent','path':str(self.path),'target':str(target),
                             'binding':self.binding,'snapshot':before},guard)
        with Directory(self.path.parent) as src, Directory(target.parent) as dst:
            def check():
                guard()
                self.verify()
            rename_noreplace(src,self.path.name,dst,target.name,check)
        require(snapshot(target) == before, 'promotion changed tree; quarantine/manual recovery')
        self.journal.append({'kind':'tree-promoted','path':str(target),'source':str(self.path),
                             'binding':self.binding,'snapshot':before},guard)
        return OwnedTree(target,self.journal,self.binding)

    def cleanup(self, guard):
        expected = self.verify()  # preflight whole tree before any deletion
        self.journal.append({'kind':'cleanup-intent','path':str(self.path),'binding':self.binding,
                             'snapshot':expected},guard)
        entries = expected['entries']
        for rel in sorted(entries,key=lambda p:(p.count('/'),p),reverse=True):
            parent_path = self.path/Path(rel).parent
            with Directory(parent_path) as parent:
                self.journal.append({'kind':'cleanup-entry-intent','path':str(self.path),'relative':rel,
                                     'binding':self.binding,'entry':entries[rel]},guard)
                guard()
                parent.check()
                info = os.stat(Path(rel).name,dir_fd=parent.fd,follow_symlinks=False)
                require(list(identity(info)) == entries[rel]['inode'], 'cleanup inode changed')
                if entries[rel]['kind'] == 'build-link':
                    require(os.readlink(Path(rel).name,dir_fd=parent.fd) == entries[rel]['target'], 'build link changed')
                    os.unlink(Path(rel).name,dir_fd=parent.fd)
                elif entries[rel]['kind'] == 'file':
                    require(digest(parent.read(Path(rel).name,256*1024*1024 if rel.startswith(('node_modules/','.next/')) else MAX_FILE)) == entries[rel]['sha256'], 'cleanup bytes changed')
                    os.unlink(Path(rel).name,dir_fd=parent.fd)
                else:
                    os.rmdir(Path(rel).name,dir_fd=parent.fd)
                os.fsync(parent.fd)
        self.journal.append({'kind':'cleanup-root-intent','path':str(self.path),'binding':self.binding,
                             'rootInode':expected['rootInode']},guard)
        with Directory(self.path.parent) as parent:
            guard()
            parent.check()
            require(list(identity(os.stat(self.path.name,dir_fd=parent.fd,follow_symlinks=False))) == expected['rootInode'],
                    'cleanup root changed')
            os.rmdir(self.path.name,dir_fd=parent.fd)
            os.fsync(parent.fd)
        self.journal.append({'kind':'tree-cleaned','path':str(self.path),'binding':self.binding},guard)
        require(not os.path.lexists(self.path), 'cleanup not complete')


def cleanup_grant_time(journal, binding, now, approval_hash):
    """Proves only the time of an existing grant. Does not authorize an effect."""
    require(type(now) is int, 'current clock snapshot required')
    seals = [r['event'] for r in journal.read() if r['event']['kind'] == 'cleanup-grant'
             and r['event'].get('binding') == binding]
    require(seals and seals[-1]['approvalHash'] == approval_hash, 'no prior cleanup grant')
    timestamp = seals[-1]['validatedAt']
    require(type(timestamp) is int and 0 <= timestamp <= now, 'invalid historical cleanup grant')
    return timestamp


class ExecutionSession:
    """Future external authorization bridge. No instance is executed in implementation tests.

    A fresh operator state (approval/revocation/current time) is read before every effect.
    No CLI switches, environment boolean or historical receipt grant executive authority.
    """
    def __init__(self, bundle, work_order, authorization, *, operator_state, control_root):
        require(callable(operator_state), 'external current operator state required')
        self.bundle = bundle
        self.work_order = work_order
        self.authorization = authorization
        self.operator_state = operator_state
        self.control_root = absolute(control_root)
        self.wo = loads(work_order)
        self.binding = {'workOrderHash':digest(work_order),
                        'generationManifestHash':object_hash(bundle['manifest']),
                        'adaptationHash':object_hash(bundle['adaptation'])}
        self.executionAuthority = 'none'  # this object is not an authorization artifact

    def revalidate(self, action):
        validate_bundle(self.bundle)
        contract('business-execution-work-order.v1',self.wo)
        state = self.operator_state()
        require(type(state) is dict and set(state) == {'approvedWorkOrderHash','approvalRef','approvalBytes',
                'revokedHashes','now','controlRoot'}, 'incomplete external operator state')
        require(type(state['now']) is int and abs(int(time.time())-state['now']) <= 2, 'stale external clock/state snapshot')
        require(state['controlRoot'] == str(self.control_root), 'control root not externally authorized')
        current = {r['path']:secure_read(ROOT/r['path']) for r in self.wo['inputHashes']}
        recipes = [loads(raw) for path,raw in current.items() if path.endswith('.json')]
        recipes = [r for r in recipes if type(r) is dict and r.get('format') == 'nexonova.business-runtime-recipe.v1']
        require(len(recipes)==1 and recipes[0].get('controlRoot')==str(self.control_root),
                'control root must be bound by exactly one executive input recipe')
        require(set(B_FILES) <= set(current), 'B code/tests must be bound in executive input hashes')
        require(self.wo['metadataHash'] == object_hash(self.bundle['metadata']), 'metadata mismatch')
        require(self.wo['planHash'] == object_hash(self.bundle['plan']), 'plan mismatch')
        validator_hash = object_hash([{'path':p,'sha256':digest(current[p])} for p in sorted(B_FILES)])
        # Registry handles consumption under its lock; the context is revalidated, not reissued.
        effective_now = state['now']
        if action == 'cleanup' and effective_now >= min(self.wo['expiresAt'],loads(self.authorization)['expiresAt']):
            # Historical validation time proves the old cleanup grant; it does not renew
            # stage/build authority. Revocation and all current hashes still apply.
            with Directory(self.control_root,private=True) as control:
                effective_now = cleanup_grant_time(Journal(control),self.binding,state['now'],digest(state['approvalBytes']))
        context = authorization_context(self.work_order,self.authorization,canonical(self.bundle['manifest']),
            canonical(self.bundle['adaptation']),approved_work_order_hash=state['approvedWorkOrderHash'],
            trusted_approval_ref=state['approvalRef'],approval_bytes=state['approvalBytes'],requested_action=action,
            now=effective_now,consumed_uses=frozenset(),revoked_hashes=state['revokedHashes'],
            current_inputs=current,current_code_hash=tree_hash(ROOT,CODE_PATHS),current_validator_hash=validator_hash)
        for destination in self.wo['destinations'].values():
            path = absolute(destination)
            require(not ROOT.is_relative_to(path), 'repository or ancestor cannot be an output')
            for source in (*CODE_PATHS,*B_FILES):
                require(not (ROOT/source).is_relative_to(path), 'output overlaps protected code')
            require(not self.control_root.is_relative_to(path) and not path.is_relative_to(self.control_root), 'control/output overlap')
            with Directory(path.parent):
                pass
        self.last_validated_at = effective_now
        self.last_approval_hash = digest(state['approvalBytes'])
        return context

    @contextlib.contextmanager
    def operation(self, action):
        self.revalidate(action)  # reject before even creating a lock or journal
        with Directory(self.control_root,private=True) as control:
            registry = UseRegistry(control)
            guard = lambda:self.revalidate(action)
            with registry.reserve(self.wo['runId'],action,self.binding,guard) as journal:
                if action != 'cleanup' and 'cleanup' in loads(self.authorization)['actions'] and 'cleanup' in self.wo['actions']:
                    journal.append({'kind':'cleanup-grant','binding':self.binding,
                                    'validatedAt':self.last_validated_at,'approvalHash':self.last_approval_hash},guard)
                yield journal,guard

    @contextlib.contextmanager
    def workflow(self, actions):
        require(actions and len(set(actions)) == len(actions), 'workflow actions missing/duplicated')
        def all_guards():
            for action in actions:
                self.revalidate(action)
        all_guards()
        with Directory(self.control_root,private=True) as control:
            with UseRegistry(control).reserve_many(self.wo['runId'],actions,self.binding,all_guards) as journal:
                if 'cleanup' in self.wo['actions'] and 'cleanup' in loads(self.authorization)['actions']:
                    journal.append({'kind':'cleanup-grant','binding':self.binding,
                                    'validatedAt':self.last_validated_at,'approvalHash':self.last_approval_hash},all_guards)
                yield journal,all_guards

    def stage(self):
        with self.operation('stage') as (journal,guard):
            tree = OwnedTree(self.wo['destinations']['staging'],journal,self.binding)
            tree.create(self.bundle['payload'],guard)
            OwnedTree(self.wo['destinations']['validation'],journal,self.binding).create(self.bundle['payload'],guard)
            return {'status':'STAGED_CANDIDATE','binding':self.binding,'executionAuthority':'none'}

    def promote(self, technical_receipt, receipt_validator):
        require(callable(receipt_validator), 'independent technical receipt consumer required')
        result = receipt_validator(technical_receipt)
        required_gates = {'database-migrations','resource-authorization','module-crud','authentication','compatibility','build-tests','cleanup'}
        require(type(result) is dict and result.get('generationManifestHash') == self.binding['generationManifestHash'] and
                type(result.get('technicalGates')) is dict and set(result['technicalGates']) == required_gates and
                all(v == 'PASS' for v in result['technicalGates'].values()),
                'technical gates incomplete/invalid')
        with self.operation('promote') as (journal,guard):
            tree = OwnedTree(self.wo['destinations']['staging'],journal,self.binding)
            tree.promote(self.wo['destinations']['output'],guard)
            return {'status':'PROMOTED_CANDIDATE_NOT_HUMAN_ACCEPTED','executionAuthority':'none'}

    def cleanup(self):
        # Expiry alone does not erase a durably recorded cleanup grant. Explicit
        # revocation, changed code/input/approval or ambiguous ownership still blocks.
        with self.operation('cleanup') as (journal,guard):
            for role in ('validation','staging'):
                path = self.wo['destinations'][role]
                if os.path.lexists(path):
                    OwnedTree(path,journal,self.binding).cleanup(guard)
            return {'status':'OWNED_TEMPORARIES_REMOVED','executionAuthority':'none'}


def recover_promoted_tree(target, journal, binding, guard):
    """Explicit crash recovery after rename but before its completion record."""
    target = absolute(target)
    candidates = [r['event'] for r in journal.read() if r['event']['kind'] == 'promote-intent'
                  and r['event'].get('target') == str(target) and r['event'].get('binding') == binding]
    require(candidates, 'no matching promotion intent')
    event = candidates[-1]
    require(not os.path.lexists(event['path']) and snapshot(target) == event['snapshot'],
            'ambiguous partial promotion; no recovery')
    journal.append({'kind':'tree-promoted','path':str(target),'source':event['path'],
                    'binding':binding,'snapshot':event['snapshot'],'recovered':True},guard)
    return OwnedTree(target,journal,binding)


def recover_cleanup(tree, guard):
    """Only absence backed by a recorded delete intent is tolerated after a crash."""
    events = [r['event'] for r in tree.journal.read() if r['event'].get('path') == str(tree.path)
              and r['event'].get('binding') == tree.binding]
    intents = [e for e in events if e['kind'] == 'cleanup-intent']
    require(intents, 'no interrupted cleanup')
    original = intents[-1]['snapshot']
    deleted = {e['relative']:e['entry'] for e in events if e['kind'] == 'cleanup-entry-intent'}
    root_intent = any(e['kind'] == 'cleanup-root-intent' and e['rootInode'] == original['rootInode'] for e in events)
    if not os.path.lexists(tree.path):
        require(root_intent, 'root disappeared without owned cleanup intent')
        tree.journal.append({'kind':'tree-cleaned','path':str(tree.path),'binding':tree.binding,'recovered':True},guard)
        return
    actual = snapshot(tree.path,build_links=any(x['kind']=='build-link' for x in original['entries'].values()))
    require(actual['rootInode'] == original['rootInode'], 'cleanup root replaced')
    require(set(actual['entries']) <= set(original['entries']), 'foreign entry during recovery')
    for path,entry in original['entries'].items():
        if path in actual['entries']:
            require(actual['entries'][path] == entry, 'remaining entry modified')
        else:
            require(deleted.get(path) == entry, 'unexplained missing entry')
    tree.journal.append({'kind':'tree-state','path':str(tree.path),'binding':tree.binding,
                         'snapshot':actual,'recoveryFrom':object_hash(original)},guard)
    tree.cleanup(guard)
