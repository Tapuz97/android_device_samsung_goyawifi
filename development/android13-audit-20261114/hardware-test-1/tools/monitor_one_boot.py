"""Observe one boot only. Never reboots or writes/logs on the tablet."""
from pathlib import Path
import datetime,json,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from recovery_transport import adb,BASE
dest=BASE/'tests/android13-complete-20261114';dest.mkdir(exist_ok=True)
start=time.monotonic();rows=[];last=None;first_id=None;status='TIMEOUT'
while time.monotonic()-start<600:
    row=dict(elapsed=round(time.monotonic()-start,1),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        state=adb('get-state',timeout=5).strip();row['adb_state']=state
        if state=='recovery':status='RETURNED_TO_RECOVERY';rows.append(row);break
        text=adb('shell', 'echo ID=$(cat /proc/sys/kernel/random/boot_id); echo UPTIME=$(cat /proc/uptime); echo SDK=$(getprop ro.build.version.sdk); echo COMPLETE=$(getprop sys.boot_completed); echo SF=$(getprop init.svc.surfaceflinger); echo AUDIO=$(getprop init.svc.audioserver); echo ZYGOTE=$(getprop init.svc.zygote); echo ANIMATION=$(getprop init.svc.bootanim); echo APEX=$(getprop apexd.status)',timeout=8)
        props=dict(line.split('=',1) for line in text.splitlines() if '=' in line);row.update(props)
        if first_id is None:first_id=props.get('ID')
        if first_id and props.get('ID')!=first_id:status='UNEXPECTED_REBOOT';rows.append(row);break
        if props.get('SDK')=='33' and props.get('COMPLETE')=='1':status='ANDROID13_REPORTS_BOOT_COMPLETED';rows.append(row);break
        short={k:props.get(k) for k in ('SDK','COMPLETE','SF','AUDIO','ZYGOTE','ANIMATION','APEX')}
        if short!=last:print(f"{row['elapsed']}s {short}",flush=True);last=short
    except Exception as exc:row['transport']=str(exc)[-180:]
    rows.append(row)
    (dest/'boot-timeline.json').write_text(json.dumps(dict(status='OBSERVING_ONE_BOOT',rows=rows),indent=2)+'\n')
    time.sleep(10)
result=dict(status=status,elapsed=round(time.monotonic()-start,1),boot_id=first_id,rows=rows,
            screen_verified=False,touch_verified=False,audible_speaker_verified=False)
(dest/'boot-timeline.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2),flush=True)
