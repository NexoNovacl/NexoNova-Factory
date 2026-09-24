# P4.4 OpenSSL preparation image

Derived from the approved Node22.23.2 image without changing its digest or any P3 policy. image-lock.json records the exact Debian snapshot packages and SHA256 checksums, recipe hash, SOURCE_DATE_EPOCH, platform and OCI/config digests. No application credentials are inputs.

Run `python3 -B scripts/prepare_auth_image.py` from Factory after explicit operator authorization for dependency/image preparation. It downloads the three public packages with TLS validation, checks their locked hashes, builds twice with no cache/network, compares both digests against the approved lock and only then loads the image locally. It never publishes an image. Different BuildKit/frontend versions must pass the same digest check or require a reviewed new lock, not silently overwrite it.

Initial package resolution used authenticated Debian InRelease metadata at snapshot20260921T000000Z. The slim image lacked a CA store, so preparation mounted only the public host CA bundle readonly for TLS verification; signatures remained enabled. Runtime does not mount host certificates. Final image contains the locked Debian ca-certificates package.

`var/cache/ldconfig/aux-cache` is deliberately removed: it contains build-specific inode metadata, is regenerable and caused the first pair of images to differ. `/etc/ld.so.cache` and the installed libraries remain. Timestamps are normalized by BuildKit's rewrite-timestamp exporter. Build references/receipts are nondeterministic evidence and are not part of the OCI image hash.

Execution uses the locally loaded RepoDigest in image-lock.json with --pull=never. Docker29 uses the OCI manifest as its image ID; configDigest is a separate field, not an interchangeable image reference. Public packages and builder cache are preparatory artifacts; no long-running service is created.
