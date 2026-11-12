"""Use the candidate only in screencap, preserving the running OS libraries."""
from pathlib import Path
import subprocess,hashlib,os,json,time
from PIL import Image
p=Path(__file__).resolve().parents[1];e=p/'evidence/remote-fixes-20261110';candidate=e/'libui-candidate'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=30,check=True):return subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout,check=check)
def sh(s,**kw):return call(['shell',s],**kw).stdout.decode().strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
before=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()
prov=json.loads((candidate/'provenance.json').read_text());assert hashlib.sha256((candidate/'libui.so').read_bytes()).hexdigest()==prov['sha256']
remote='/data/local/tmp/t110-import-only-candidate';sh('mkdir -p '+remote)
call(['push',candidate/'libui.so',remote+'/libui.so'])
assert sh('sha256sum '+remote+'/libui.so').split()[0]==prov['sha256']
sh('input keyevent WAKEUP; wm dismiss-keyguard; input keyevent HOME');time.sleep(2)
result=call(['shell','LD_LIBRARY_PATH='+remote+' timeout 15 /system/bin/screencap -p '+remote+'/framework.png'],timeout=25,check=False)
(e/'capture-candidate-command.txt').write_bytes(result.stdout+b'\nSTDERR\n'+result.stderr)
record={'returncode':result.returncode,'boot_server_before':before,'candidate_sha256':prov['sha256'],'system_library_replaced':False,'additional_boots':0}
try:
    call(['pull',remote+'/framework.png',e/'framework-capture-fixed.png'])
    with Image.open(e/'framework-capture-fixed.png') as im:
        im.load();record['dimensions']=list(im.size);record['colors']=len(im.getcolors(im.width*im.height) or [])
        assert im.size==(600,1024) and record['colors']>32
    assert result.returncode==0
    # A decodable PNG can still contain tiled/incorrect pixels. Review the
    # saved image before qualifying screenshot functionality.
    record['status']='CAPTURE_RETURNED_CONTENT_REQUIRES_VISUAL_REVIEW'
finally:
    record['boot_server_after']=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()
    assert record['boot_server_after']==before
    (e/'import-only-hardware-test.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
