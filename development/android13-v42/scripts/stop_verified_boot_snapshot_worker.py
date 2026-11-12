"""Stop only our identified snapshot writer, preserving init and saved logs."""
from pathlib import Path
import json,os,re,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112';receipt=e/'v41-boot-logger-stopped.json';assert not receipt.exists()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd,check=True):
    r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=30)
    if check:assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
    return r.stdout.decode(errors='replace').replace('\r','').strip()
install=json.loads((e/'v41-installation.json').read_text());assert sh('cat /proc/sys/kernel/random/boot_id')==install['boot_id']
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
processes=sh('ps -A');(e/'v41-processes-before-logger-stop.txt').write_text(processes)
candidates=[]
for line in processes.splitlines():
    columns=line.split()
    if len(columns)>3 and columns[-1] in ['init','/init'] and columns[1].isdigit():
        pid=int(columns[1])
        if pid<=1:continue
        executable=sh('readlink /proc/'+str(pid)+'/exe')
        if executable!='/init':continue
        fds=sh('ls -l /proc/'+str(pid)+'/fd')
        required=['/kernel-0.txt','/kernel-1.txt','/logger-status.txt']
        if all(name in fds for name in required) and '/t110-bootlogs/boot-' in fds:
            candidates.append(dict(pid=pid,executable=executable,fds=fds))
assert len(candidates)==1,('No uniquely identified diagnostic snapshot writer',candidates)
worker=candidates[0];assert worker['pid']!=1
server=sh('pidof system_server');root_init=sh('readlink /proc/1/exe')
sh('kill -TERM '+str(worker['pid']))
assert sh('pidof system_server')==server and sh('readlink /proc/1/exe')==root_init
record=dict(status='VERIFIED_DIAGNOSTIC_SNAPSHOT_WRITER_STOPPED',boot_id=install['boot_id'],worker=worker,
            root_init_untouched=True,system_server_untouched=True,saved_logs_preserved=True,reboot=False,ui_fixed=False)
receipt.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='worker'},indent=2))
