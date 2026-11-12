"""Read-only Git object and tracked-file audit after the USB I/O incident."""
import concurrent.futures
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time

ROOT = Path('/root/t110-build/lineage20')
EVIDENCE = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/evidence')
assert os.environ.get('WSL_DISTRO_NAME') == 'T110Build'
started = time.time()
projects = (ROOT / '.repo/project.list').read_text().splitlines()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--after-enclosure', action='store_true')
args = parser.parse_args()
label = 'after-enclosure' if args.after_enclosure else 'after-cable'
cached = {}
if args.after_enclosure:
    previous = [json.loads(line) for line in (EVIDENCE/'source-integrity-after-cable.jsonl').read_text().splitlines()]
    assert len(previous) == len(projects) and {row['project'] for row in previous} == set(projects)
    clean = [row for row in previous if row['fsck_exit'] == 0 and not row['errors']]
    # Repeat the largest reads through the new bridge, in addition to every
    # project interrupted by the original I/O fault.
    clean.sort(key=lambda row: row['checked_bytes'], reverse=True)
    cached = {row['project']: row for row in clean[12:]}

def inspect(relative):
    repo = ROOT / relative
    result = {'project': relative, 'checked_files': 0, 'checked_bytes': 0,
              'changes': [], 'errors': []}
    try:
        fsck = subprocess.run(['git', '-C', str(repo), 'fsck', '--full', '--no-reflogs', '--no-dangling'],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
        result['fsck_exit'] = fsck.returncode
        if fsck.stdout:
            result['fsck_output'] = fsck.stdout.decode(errors='replace')[-12000:]
        listing = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '--stage', '-z'])
        for entry in listing.split(b'\0'):
            if not entry:
                continue
            metadata, name = entry.split(b'\t', 1)
            mode, expected, stage = metadata.split()
            if mode == b'160000':
                continue
            assert stage == b'0', (relative, name, stage)
            path = repo / os.fsdecode(name)
            try:
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode):
                    data = os.fsencode(os.readlink(path))
                    digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data)
                else:
                    assert stat.S_ISREG(info.st_mode), path
                    digest = hashlib.sha1(b'blob ' + str(info.st_size).encode() + b'\0')
                    with path.open('rb') as handle:
                        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                            digest.update(chunk)
                actual = digest.hexdigest()
                result['checked_files'] += 1
                result['checked_bytes'] += info.st_size
                if actual != expected.decode():
                    result['changes'].append({'path': os.fsdecode(name), 'expected': expected.decode(), 'actual': actual})
            except Exception as exc:
                result['errors'].append({'path': os.fsdecode(name), 'error': repr(exc)})
    except Exception as exc:
        result['errors'].append({'error': repr(exc)})
    return result

results = list(cached.values())
fresh = [p for p in projects if p not in cached]
print(f'{len(fresh)} projects to read now; {len(cached)} prior successful checks retained', flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    jobs = [pool.submit(inspect, p) for p in fresh]
    for future in concurrent.futures.as_completed(jobs):
        result = future.result()
        results.append(result)
        with (EVIDENCE / f'source-integrity-{label}.jsonl').open('a') as log:
            log.write(json.dumps(result) + '\n')
        if len(results) % 20 == 0 or result['errors'] or result.get('fsck_exit', 1):
            print(f"{len(results)}/{len(projects)} projects, {time.time()-started:.0f}s; latest={result['project']} errors={len(result['errors'])} fsck={result.get('fsck_exit')}", flush=True)
summary = {'elapsed_seconds': time.time()-started, 'projects': len(results),
           'reused_previous_successes': len(cached), 'fresh_projects': len(fresh),
           'fresh_bytes': sum(r['checked_bytes'] for r in results[len(cached):]),
           'files': sum(r['checked_files'] for r in results),
           'bytes': sum(r['checked_bytes'] for r in results),
           'failed_projects': [r for r in results if r['errors'] or r.get('fsck_exit', 1)],
           'changed_projects': [r for r in results if r['changes']]}
(EVIDENCE / f'source-integrity-{label}.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({**summary, 'failed_projects': len(summary['failed_projects']), 'changed_projects': len(summary['changed_projects'])}, indent=2), flush=True)
raise SystemExit(bool(summary['failed_projects']))
