from pathlib import Path
import os,subprocess,json,shlex,re
from PIL import Image
p=Path(__file__).resolve().parents[1];out=p/'evidence/offline-v32/readback';out.mkdir(exist_ok=True)
base=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
r=subprocess.check_output(base+['shell','test -f /init.t110-core.rc && cat /sys/block/mmcblk0/device/cid'],timeout=10);assert r.decode().strip()=='1101003030384745T110_ADB_SERIAL'
pid=subprocess.check_output(base+['shell','pidof zygote'],timeout=10).decode().split()[0];assert pid.isdigit()
raw=subprocess.check_output(base+['exec-out','cat /proc/'+pid+'/environ'],timeout=10)
env={}
for field in raw.decode().split('\0'):
    if '=' in field:
        key,value=field.split('=',1)
        if key in ['BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','ANDROID_ART_ROOT','ANDROID_I18N_ROOT','ANDROID_TZDATA_ROOT']:env[key]=value
assert env.get('BOOTCLASSPATH')
prefix=' '.join(k+'='+shlex.quote(v) for k,v in env.items())
results=[]
for mode,w,h in [('software',600,1024),('hardware',600,1024),('hardware',1024,600)]:
    label=f'{mode}-{w}x{h}';remote='/data/local/tmp/t110-readback-'+label+'.raw'
    command=prefix+f' CLASSPATH=/data/local/tmp/t110-readback-probe.jar timeout 30 app_process /system/bin T110CanvasReadback {mode} {w} {h} {remote}'
    r=subprocess.run(base+['shell',command],capture_output=True,timeout=40)
    log=(r.stdout+r.stderr).decode(errors='replace');(out/(label+'.txt')).write_text(log)
    print(label,r.returncode,log,flush=True)
    match=re.search(r'READBACK (\d+) (\d+) (\d+) (\d+) (\d+)',log)
    result=dict(mode=mode,width=w,height=h,returncode=r.returncode)
    if match:
        iw,ih,stride,pixel,size=map(int,match.groups());assert(iw,ih,pixel)==(w,h,4)
        data=subprocess.check_output(base+['exec-out','cat '+remote],timeout=15);assert len(data)==size
        (out/(label+'.raw')).write_bytes(data)
        data=data+b'\0'*(stride*h-len(data))
        img=Image.frombytes('RGBA',(w,h),data,'raw','RGBA',stride)
        img.save(out/(label+'.png'))
        result['samples']=[img.getpixel((x*w//4,y*h//4)) for y in (1,3) for x in (1,3)]
        result['stride']=stride
    results.append(result)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
