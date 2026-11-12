from pathlib import Path
import os,subprocess,json,time,shlex
p=Path(__file__).resolve().parents[1];trial=p/'hardware-tests/20261107-151636-core'
base=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
assert subprocess.check_output(base+['shell','test -f /init.t110-core.rc && cat /sys/block/mmcblk0/device/cid'],timeout=10).decode().strip()=='1101003030384745T110_ADB_SERIAL'
pid=subprocess.check_output(base+['shell','pidof zygote'],timeout=10).decode().split()[0];assert pid.isdigit()
raw=subprocess.check_output(base+['exec-out','cat /proc/'+pid+'/environ'],timeout=10)
env={}
for field in raw.decode().split('\0'):
    if '=' in field:
        key,value=field.split('=',1)
        if key in ['BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','ANDROID_ART_ROOT','ANDROID_I18N_ROOT','ANDROID_TZDATA_ROOT']:env[key]=value
assert env.get('BOOTCLASSPATH')
prefix=' '.join(k+'='+shlex.quote(v) for k,v in env.items());results=[]
subprocess.run(base+['shell','setprop debug.hwui.use_partial_updates true'],timeout=10,check=True)
for usage in ['0xb00','0xb03']:
    label='buffer-usage-'+usage
    subprocess.run(base+['shell','input keyevent 224'],timeout=10,check=True)
    command=prefix+f' CLASSPATH=/data/local/tmp/t110-buffer-display.jar timeout 35 app_process /system/bin T110BufferDisplay {usage}'
    process=subprocess.Popen(base+['shell',command],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace')
    posted=False
    with (trial/(label+'.txt')).open('w') as log:
        for line in process.stdout:
            log.write(line);log.flush()
            if 'BUFFER_POSTED' in line:
                posted=True;print(line.strip(),flush=True);time.sleep(2)
                subprocess.run(['python',str(p/'scripts/capture_v26_framebuffer.py'),str(trial),'--label',label],check=True,timeout=20)
                sf=subprocess.run(base+['shell','dumpsys SurfaceFlinger'],capture_output=True,timeout=12)
                (trial/(label+'-sf.txt')).write_bytes(sf.stdout)
            elif 'Exception' in line:print(line.strip(),flush=True)
    code=process.wait(timeout=5);results.append(dict(usage=usage,posted=posted,returncode=code));print(label,code,flush=True)
    assert code==0 and posted,(label,code)
(trial/'buffer-usage-comparison.json').write_text(json.dumps(results,indent=2)+'\n')
