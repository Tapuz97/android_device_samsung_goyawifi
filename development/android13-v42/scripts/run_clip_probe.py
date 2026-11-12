from pathlib import Path
import os, subprocess, shlex, zipfile, sys
p = Path(__file__).resolve().parents[1]
e = p/'evidence/offline-v40/clip-probe'; e.mkdir(parents=True, exist_ok=True)
sdk = Path(os.environ['LOCALAPPDATA'])/'Android/Sdk'
lib = sdk/'platforms/android-36/android.jar'
classes = e/'classes'; classes.mkdir(exist_ok=True)
subprocess.run(['javac','--release','8','-cp',str(lib),'-d',str(classes),str(p/'scripts/T110ClipProbe.java')],check=True)
subprocess.run(['java','-cp',str(sdk/'build-tools/36.0.0/lib/d8.jar'),'com.android.tools.r8.D8',
                '--min-api','33','--lib',str(lib),'--output',str(e),str(classes/'T110ClipProbe.class')],check=True)
with zipfile.ZipFile(e/'probe.jar','w') as z: z.write(e/'classes.dex','classes.dex')
adb = [str(sdk/'platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
subprocess.run(adb+['push',str(e/'probe.jar'),'/data/local/tmp/t110-clip-probe.jar'],check=True,capture_output=True)
pid=subprocess.check_output(adb+['shell','pidof zygote']).decode().split()[0]; assert pid.isdigit()
raw=subprocess.check_output(adb+['exec-out','cat /proc/'+pid+'/environ']).decode()
env={}
for entry in raw.split('\0'):
    if '=' in entry:
        k,v=entry.split('=',1)
        if k in ['BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','ANDROID_ART_ROOT','ANDROID_I18N_ROOT','ANDROID_TZDATA_ROOT']: env[k]=v
assert env.get('BOOTCLASSPATH')
prefix=' '.join(k+'='+shlex.quote(v) for k,v in env.items())
command=prefix+' CLASSPATH=/data/local/tmp/t110-clip-probe.jar:/system/framework/content.jar timeout 120 app_process /system/bin T110ClipProbe'
if len(sys.argv)>1: command+=' '+shlex.join(sys.argv[1:])
r=subprocess.run(adb+['shell',command],capture_output=True,timeout=135)
(e/'last-result.txt').write_bytes(r.stdout+r.stderr)
print(r.stdout.decode(errors='replace')); print(r.stderr.decode(errors='replace'))
assert r.returncode==0, r.returncode
