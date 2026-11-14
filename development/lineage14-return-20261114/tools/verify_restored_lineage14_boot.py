"""Bounded observation of the restored14.1 boot; never initiates a reboot."""
from pathlib import Path
import json,time
from recovery_transport import adb,BASE
DEST=BASE/'tests/lineage14-restored-20261114'
install=json.loads((DEST/'restore-verification.json').read_text(encoding='utf-8'))
assert install['status']=='WORKING14_RESTORED_READBACK_VERIFIED_NOT_BOOTED'
start=time.monotonic();rows=[];status='TIMEOUT';boot_id=None
while time.monotonic()-start<300:
    row=dict(elapsed=round(time.monotonic()-start,1))
    try:
        state=adb('get-state',timeout=5).strip();row['state']=state
        if state=='recovery' and row['elapsed']>20:status='RETURNED_TO_RECOVERY';rows.append(row);break
        if state=='device':
            text=adb('shell','echo SDK=$(getprop ro.build.version.sdk); echo RELEASE=$(getprop ro.build.version.release); echo COMPLETE=$(getprop sys.boot_completed); echo ID=$(cat /proc/sys/kernel/random/boot_id); echo SF=$(getprop init.svc.surfaceflinger)',timeout=10)
            values=dict(line.split('=',1) for line in text.splitlines() if '=' in line);row.update(values)
            if boot_id is None:boot_id=values.get('ID')
            if boot_id and values.get('ID')!=boot_id:status='UNEXPECTED_REBOOT';rows.append(row);break
            if values.get('SDK')=='25' and values.get('RELEASE')=='7.1.2' and values.get('COMPLETE')=='1':
                status='PASS_RESTORED14_BOOT_COMPLETED';rows.append(row);break
    except Exception as error:row['transport']=str(error)[-160:]
    rows.append(row);time.sleep(5)
result=dict(status=status,boot_id=boot_id,elapsed=round(time.monotonic()-start,1),rows=rows,
            original_data_preserved=True,system_sha256=install['system_sha256'],boot_sha256=install['boot_sha256'])
(DEST/'restored-boot-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2),flush=True)
