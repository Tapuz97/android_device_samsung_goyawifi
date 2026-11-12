"""Trace only the temporary QA process while reproducing the codec start fault."""
from pathlib import Path
import subprocess,os,time,threading,sys,json
p=Path(__file__).resolve().parents[1];e=p/'evidence/remote-fixes-20261110'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s):return subprocess.run(adb+['shell',s],capture_output=True,timeout=20).stdout.decode().strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
sh('am force-stop dev.tapuz.t110.audit')
remote='/data/local/tmp/t110-codec-alloc.trace';state={};stop=threading.Event()
def trace():
    while not stop.is_set():
        pid=sh('pidof dev.tapuz.t110.audit')
        if pid:
            assert pid.isdecimal()
            assert sh('cat /proc/'+pid+'/cmdline').strip('\0')=='dev.tapuz.t110.audit'
            state['qa_pid']=pid
            proc=subprocess.Popen(adb+['shell','strace -f -tt -e trace=open,openat,ioctl,mmap2 -o '+remote+' -p '+pid],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            state['trace_process']=proc
            return
        time.sleep(.15)
worker=threading.Thread(target=trace);worker.start()
try:
    result=subprocess.run([sys.executable,str(p/'scripts/run_functional_app_probe.py'),'--evidence','remote-fixes-20261110'],capture_output=True,timeout=240)
    (e/'codec-trace-runner.txt').write_bytes(result.stdout+b'\nSTDERR\n'+result.stderr)
finally:
    stop.set();worker.join(25)
    for pid in sh('pidof strace').split():
        cmd=sh('cat /proc/'+pid+'/cmdline')
        if remote in cmd:sh('kill -INT '+pid)
    proc=state.pop('trace_process',None)
    if proc:
        try:out,err=proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:proc.terminate();out,err=proc.communicate(timeout=5)
        (e/'codec-strace-status.txt').write_bytes(out+b'\nSTDERR\n'+err)
subprocess.run(adb+['pull',remote,str(e/'codec-alloc.trace')],check=True,capture_output=True,timeout=30)
(e/'codec-trace-context.json').write_text(json.dumps(state,indent=2)+'\n')
print('QA_CODEC_ALLOCATION_TRACE_SAVED',result.returncode)
