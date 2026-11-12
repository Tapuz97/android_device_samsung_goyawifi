from pathlib import Path
import subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35'
base='/root/t110-build/lineage20'
files=['frameworks/base/libs/hwui/renderthread/EglManager.cpp','frameworks/base/libs/hwui/pipeline/skia/SkiaOpenGLPipeline.cpp']
for f in files:
 r=subprocess.run(['wsl.exe','-d','T110Build','--','cat',base+'/'+f],capture_output=True,timeout=90)
 assert r.returncode==0,r.stderr.decode(errors='replace')
 (e/('source-'+Path(f).name)).write_bytes(r.stdout)
 print(f,len(r.stdout))
