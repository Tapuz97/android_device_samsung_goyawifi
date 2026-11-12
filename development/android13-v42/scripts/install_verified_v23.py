"""Install the verified combined build and run exactly one normal Android boot."""
from pathlib import Path
import json,subprocess,sys
p=Path(__file__).resolve().parents[1]
for script in ['prepare_v23_recovery.py','stage_v23_system.py']:
    subprocess.run([sys.executable,str(p/'scripts'/script)],check=True)
pair=json.loads((p/'artifacts/lineage20-rom-v23/rom-pair.json').read_text())
subprocess.run([sys.executable,str(p/'scripts/run_core_boot_tablet.py'),
    str(p/'artifacts/android13-full-v27'),'--sha256',pair['boot_sha256'],
    '--full','--system-md5',pair['system_md5'],'--from-recovery',
    '--expected-boot-md5',pair['boot_md5'],'--reuse-boot','--stability-seconds','180'],check=True)
