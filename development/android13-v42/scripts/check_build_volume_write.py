"""Bounded file-level write/fsync/read check, only in the dedicated build root."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

assert os.environ.get('WSL_DISTRO_NAME') == 'T110Build'
base = Path('/root/t110-build').resolve(strict=True)
assert str(base) == '/root/t110-build'
device = subprocess.check_output(['findmnt', '-n', '-o', 'SOURCE', '/'], text=True).strip()
assert subprocess.check_output(['blkid', '-s', 'UUID', '-o', 'value', device], text=True).strip() == '897592f3-1bd0-4be7-8abf-2b090bb91093'
assert shutil.disk_usage(base).free > 16 * 1024**3
evidence = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/evidence')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--after-enclosure', action='store_true')
args = parser.parse_args()
label = 'enclosure' if args.after_enclosure else 'cable'
fd, name = tempfile.mkstemp(prefix='cable-write-probe-', dir=base)
path = Path(name)
assert path.parent == base
started = time.time()
expected = hashlib.sha256()
size = 2 * 1024**3
try:
    with os.fdopen(fd, 'wb', buffering=0) as handle:
        for offset in range(0, size, 4 * 1024**2):
            block = hashlib.shake_256(b'T110 cable check ' + str(offset).encode()).digest(4 * 1024**2)
            assert handle.write(block) == len(block)
            expected.update(block)
        os.fsync(handle.fileno())
        os.posix_fadvise(handle.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)
    print('2 GiB written and fsynced; reading back', flush=True)
    actual = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024**2), b''):
            actual.update(block)
    result = {'bytes': size, 'expected_sha256': expected.hexdigest(), 'readback_sha256': actual.hexdigest(),
              'pass': expected.digest() == actual.digest(), 'elapsed_seconds': time.time()-started,
              'scope': 'File write/fsync/read after Linux page-cache eviction; host/device caches not bypassed; not a physical-media health certification'}
    (evidence / f'e-{label}-write-readback.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    assert result['pass'], 'Written-file readback mismatch'
finally:
    path.unlink()
