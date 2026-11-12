"""Archive the combined alarm-timer kernel/module and exact incremental patch."""
from pathlib import Path
import difflib,hashlib,json,shutil,subprocess
base=Path('/root/t110-build')
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
source=base/'kernel-alarm'
parent=base/'kernel-random'
out=base/'out-alarm'
dest=project/'artifacts/kernel-alarm'
dest.mkdir(exist_ok=False)
patch=[]
for name in ['include/linux/alarmtimer.h','kernel/time/alarmtimer.c','fs/timerfd.c']:
    a=(parent/name).read_text().splitlines(keepends=True)
    b=(source/name).read_text().splitlines(keepends=True)
    patch.extend(difflib.unified_diff(a,b,fromfile='a/'+name,tofile='b/'+name))
patchpath=project/'patches/0035-kernel-alarm-and-boottime-timerfd.patch'
patchpath.write_text(''.join(patch))
subprocess.run(['patch','--dry-run','-R','-p1','-i',str(patchpath)],cwd=source,check=True)
modules=list(out.rglob('galcore.ko'))
assert len(modules)==1,modules
mapping={'zImage':out/'arch/arm/boot/zImage','galcore.ko':modules[0],
         'kernel.config':out/'.config','build.log':base/'logs/alarm-tablet-build.log',
         'qemu.config':base/'out-qemu-alarm/.config'}
files={}
for name,path in mapping.items():
    shutil.copyfile(path,dest/name)
    data=(dest/name).read_bytes()
    files[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
log=(project/'evidence/qemu-alarm-test.log').read_bytes()
assert b'T110_ALARM_REGRESSION_PASS' in log and b'ALARM_FAIL' not in log
assert (out/'.config').read_bytes()==(base/'out-random/.config').read_bytes(), 'tablet configuration drift'
result=dict(status='COMPILED_ALARM_TIMERFD_REGRESSION_PASSED_HARDWARE_PENDING',
    files=files,parent_kernel='artifacts/kernel-random/provenance.json',
    incremental_patch=str(patchpath.relative_to(project)),
    patch_sha256=hashlib.sha256(patchpath.read_bytes()).hexdigest(),
    upstream_commits=['6cffe00f7d4e24679eae6b7aae4caaf915288256',
                      '11ffa9d6065f344a9bd769a2452f26f2f671e5f8',
                      '4a2378a943f09907fb1ae35c15de917f60289c14'],
    additional_change='Require CAP_WAKE_ALARM for creating alarm timerfds',
    validation=['evidence/qemu-alarm-test.log'],
    hardware_validated=False,suspend_wakeup_validated=False,
    note='QEMU exercises active timerfd behavior. Physical RTC suspend wake remains untested.')
(dest/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
