#!/usr/bin/env python3
"""Secondary scan of persisted final evidence. Synthetic-value scans ran before cleanup."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
patterns=[r'postgres(?:ql)?://[^\s"\\]+:[^\s"\\]+@',r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----',r'(?i)(?:set-cookie|authorization):\s*[^\s]',r'(?i)session_token=[A-Za-z0-9%_.+/-]{16,}',r'"(?:password|token|secret|BOOTSTRAP_DATABASE_URL|BETTER_AUTH_SECRET)"\s*:\s*"[^"\n]{16,}"']
files=list((ROOT/'docs/migration/p4-4-b-continuation').glob('*.json'))+[ROOT/'docs/migration'/n for n in ['P4_4_B_FINAL_RECEIPT.json','P4_4_B_FINAL_REPORT.md','P4_4_B_CONTINUATION_PRESERVATION.json','P4_4_B_CONTINUATION_DOCKER.json','P4_4_B_HOST_INITIAL.json','P4_4_B_HOST_FINAL.json','P4_4_B_TEMP_CLEANUP.json']]
rows=[]
for p in files:
 text=p.read_text();count=sum(len(re.findall(pattern,text)) for pattern in patterns)
 rows.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'matches':count})
report={'status':'PASS' if all(r['matches']==0 for r in rows) else 'FAIL','scope':'Persisted continuation receipts plus final JSON/report/evidence; no raw matches emitted','method':'Secondary patterns for credential URLs, private keys, auth headers, session cookies and sensitive JSON values; complements exact in-memory synthetic-value scans in each run','limitations':'Heuristic scan is not an exhaustive secret audit; no HAR or credential screenshots were created','validatorSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'files':rows}
(ROOT/'docs/migration/P4_4_B_FINAL_ARTIFACT_SCAN.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['status'],len(rows),'artifacts');sys.exit(0 if report['status']=='PASS' else 1)
