"""Resume only after completed source integrity and storage checks; retain old output."""
import datetime
import argparse
import json
import os
from pathlib import Path
import subprocess

assert os.environ.get('WSL_DISTRO_NAME') == 'T110Build'
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
evidence = project/'evidence'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--after-enclosure', action='store_true')
parser.add_argument('--incremental', action='store_true', help='Keep output after a diagnosed build-tool error')
parser.add_argument('--jobs', type=int, choices=(2, 4, 8), default=2)
args = parser.parse_args()
review_name = 'source-integrity-review-after-enclosure.json' if args.after_enclosure else 'source-integrity-review.json'
write_name = 'e-enclosure-write-readback.json' if args.after_enclosure else 'e-cable-write-readback.json'
fsck_name = 'e-native-vhdx-fsck-after-enclosure-repair.log' if args.after_enclosure else 'e-native-vhdx-fsck-readonly.log'
review = json.loads((evidence/review_name).read_text())
write = json.loads((evidence/write_name).read_text())
assert review['pass'] and write['pass']
assert 'E2FSCK_EXIT=0' in (evidence/fsck_name).read_text()
device = subprocess.check_output(['findmnt', '-n', '-o', 'SOURCE', '/'], text=True).strip()
assert subprocess.check_output(['blkid', '-s', 'UUID', '-o', 'value', device], text=True).strip() == '897592f3-1bd0-4be7-8abf-2b090bb91093'
base = Path('/root/t110-build').resolve(strict=True)
old = base/'out-system'
assert not old.is_symlink() and old.resolve() == Path('/root/t110-build/out-system')
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
quarantine = base/('out-system-before-storage-recovery-'+stamp)
assert quarantine.parent == base and not quarantine.exists()
if old.exists() and not args.incremental:
    old.rename(quarantine)
state_path = project/'BUILD-WORKSPACE.json'
state = json.loads(state_path.read_text(encoding='utf-8-sig'))
state.update(state='FULL SYSTEM BUILD RUNNING after clean offline fsck, complete source integrity review and 2 GiB write/readback check',
             restarted_at=stamp, build_jobs=args.jobs,
             active_build_log=f'T110Build:/root/t110-build/logs/system-image-{stamp}.log',
             integrity_evidence='evidence/'+review_name,
             write_readback_evidence='evidence/'+write_name)
if not args.incremental:
    state['quarantined_output'] = str(quarantine)
state.pop('build_exit', None)
state.pop('image_fit_exit', None)
state.pop('image_fit_report', None)
state['fit_check'] = 'Runs automatically after successful build'
state_path.write_text(json.dumps(state, indent=2)+'\n')
print('Resuming existing build output' if args.incremental else 'Retained previous output at '+str(quarantine), flush=True)
env = {**os.environ, 'T110_SYSTEM_JOBS': str(args.jobs), 'T110_SYSTEM_LOG_STAMP': stamp}
run = subprocess.run(['bash', str(project/'scripts/build_system_image.sh')], env=env)
state = json.loads(state_path.read_text())
state.update(build_exit=run.returncode, state='SYSTEMIMAGE BUILD FINISHED; NOT HARDWARE QUALIFIED' if run.returncode == 0 else 'SYSTEMIMAGE BUILD STOPPED WITH ERROR; inspect latest build log')
state_path.write_text(json.dumps(state, indent=2)+'\n')
if run.returncode:
    raise SystemExit(run.returncode)

image = base/'out-system/target/product/t110_bringup/system.img'
report = evidence/f'system-image-fit-{stamp}.json'
fit = subprocess.run(['python3', str(project/'scripts/verify_system_image_fit.py'),
                      str(image), '--report', str(report)])
state.update(image_fit_exit=fit.returncode,
             image_fit_report=str(report.relative_to(project)) if report.exists() else None,
             state='SYSTEMIMAGE FIT AND EXT4 VERIFIED; boot integration pending' if fit.returncode == 0 else 'SYSTEMIMAGE VERIFICATION FAILED; inspect build output and fit report')
state_path.write_text(json.dumps(state, indent=2)+'\n')
raise SystemExit(fit.returncode)
