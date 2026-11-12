"""Package matching boot inputs only after the combined system passes checks."""
from pathlib import Path
import hashlib,json,subprocess,sys
project=Path(__file__).resolve().parents[1]
assert json.loads((project/'evidence/v13-combined-fixes-contents.json').read_text())['status']=='PASS'
assert json.loads((project/'artifacts/lineage20-rom-v13/host-verification.json').read_text())['status']=='VERIFIED'
kernel=project/'artifacts/kernel-alarm'
meta=json.loads((kernel/'provenance.json').read_text())
frozen=project/'work/core-boot/v23-init.environ.rc'
frozen.write_bytes((project/'work/core-boot/init.environ.rc').read_bytes())
subprocess.run([sys.executable,str(project/'scripts/package_core_boot.py'),str(frozen),
    str(project/'artifacts/android13-full-v23'),'--full',
    '--kernel',str(kernel/'zImage'),'--kernel-sha256',meta['files']['zImage']['sha256'],
    '--module',str(kernel/'galcore.ko'),'--module-sha256',meta['files']['galcore.ko']['sha256']],check=True)
for name in ['0038-renderengine-t110-egl-window-bridge.patch','0039-art-zygote-visibility-checkpoint-lock.patch']:
    print(name,hashlib.sha256((project/'patches'/name).read_bytes()).hexdigest())
