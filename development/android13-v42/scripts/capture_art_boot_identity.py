"""Record the installed boot-image identity before compiling private app code."""
from pathlib import Path
import os, subprocess
p=Path(__file__).resolve().parents[1]
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
r=subprocess.run(adb+['shell','sha256sum /system/framework/arm/boot*.art /system/framework/org.apache.http.legacy.jar /system_ext/framework/androidx.window.extensions.jar /system_ext/framework/androidx.window.sidecar.jar'],capture_output=True,timeout=120)
assert r.returncode==0,r.stderr.decode(errors='replace')
out=r.stdout.decode().replace('\r','')
assert len(out.splitlines())>5
(p/'evidence/ui-system-hang-20261112/runtime-art-inputs.sha256').write_text(out)
print('Installed ART image and optional-library hashes saved')
