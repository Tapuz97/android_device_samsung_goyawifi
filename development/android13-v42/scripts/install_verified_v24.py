"""Install the verified combined build and run exactly one normal Android boot."""
from pathlib import Path
import json,subprocess,sys
p=Path(__file__).resolve().parents[1]
for script in ['prepare_v24_recovery.py','stage_v24_system.py']:
    subprocess.run([sys.executable,str(p/'scripts'/script)],check=True)
pair=json.loads((p/'artifacts/lineage20-rom-v24/rom-pair.json').read_text())
subprocess.run([sys.executable,str(p/'scripts/run_core_boot_tablet.py'),
    str(p/'artifacts/android13-full-v28'),'--sha256',pair['boot_sha256'],
    '--full','--system-md5',pair['system_md5'],'--from-recovery',
    '--expected-boot-md5','942182cefec3cb7666096499220789d0','--stability-seconds','180'],check=True)
