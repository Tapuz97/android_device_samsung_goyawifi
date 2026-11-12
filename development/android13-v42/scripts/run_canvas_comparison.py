from pathlib import Path
import os,subprocess,json,time,shlex
p=Path(__file__).resolve().parents[1];trial=p/'hardware-tests/20261107-151636-core'
base=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
r=subprocess.run(base+['shell','test -f /init.t110-core.rc && cat /sys/block/mmcblk0/device/cid'],capture_output=True,timeout=10,check=True);assert r.stdout.decode().strip()=='1101003030384745T110_ADB_SERIAL'
results=[]
pid=subprocess.check_output(base+['shell','pidof zygote'],timeout=10).decode().split()[0];assert pid.isdigit()
raw=subprocess.check_output(base+['exec-out','cat /proc/'+pid+'/environ'],timeout=10)
env={}
for field in raw.decode().split('\0'):
    if '=' in field:
        key,value=field.split('=',1)
        if key in ['BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','ANDROID_ART_ROOT','ANDROID_I18N_ROOT','ANDROID_TZDATA_ROOT']:env[key]=value
assert env.get('BOOTCLASSPATH')
prefix=' '.join(k+'='+shlex.quote(v) for k,v in env.items())
for mode,w,h in [('hardware',600,1024),('hardware',1024,600)]:
    label=f'canvas-settled-{mode}-{w}x{h}';posted=False
    subprocess.run(base+['shell','input keyevent 224'],capture_output=True,timeout=10,check=True)
    command=prefix+f' CLASSPATH=/data/local/tmp/t110-canvas-probe.jar timeout 50 app_process /system/bin T110CanvasProbe {mode} {w} {h}'
    process=subprocess.Popen(base+['shell',command],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace')
    with (trial/(label+'.txt')).open('w') as log:
        for line in process.stdout:
            log.write(line);log.flush()
            if 'CANVAS_POSTED' in line:
                posted=True;print(line.strip(),flush=True)
                time.sleep(4)
                subprocess.run(['python',str(p/'scripts/capture_v26_framebuffer.py'),str(trial),'--label',label],check=True,timeout=20)
                sf=subprocess.run(base+['shell','dumpsys SurfaceFlinger'],capture_output=True,timeout=12)
                (trial/(label+'-sf.txt')).write_bytes(sf.stdout)
            elif 'Exception' in line or 'Error' in line:print(line.strip(),flush=True)
    code=process.wait(timeout=5);results.append(dict(mode=mode,size=[w,h],posted=posted,returncode=code));print(label,code,flush=True)
    assert code==0 and posted,(label,code)
(trial/'canvas-comparison.json').write_text(json.dumps(dict(results=results,additional_boots=0,persistent_config_changes=False),indent=2)+'\n')
