"""After successful compilation, verify/export v23 and install it without a pause."""
from pathlib import Path
import subprocess,sys

p=Path(__file__).resolve().parents[1]
linux='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/scripts/'
log='system-image-20261107T144041Z.log'
# Require this build's actual success marker before archiving its output.
subprocess.run(['wsl','-d','T110Build','--exec','grep','-q',
    'build completed successfully','/root/t110-build/logs/'+log],check=True)
for args in [
    ['bash',linux+'archive_graphics_system.sh','lineage20-rom-v23',log],
    ['python3',linux+'verify_v23_contents.py'],
]:
    subprocess.run(['wsl','-d','T110Build','--exec']+args,check=True)
subprocess.run([sys.executable,str(p/'scripts/finalize_v23_offline.py')],check=True)
subprocess.run(['wsl','--terminate','T110Build'],check=True)
subprocess.run([sys.executable,str(p/'scripts/install_verified_v23.py')],check=True)
