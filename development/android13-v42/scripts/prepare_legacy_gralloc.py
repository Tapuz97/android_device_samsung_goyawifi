"""Apply the reviewed T110 retained-buffer patch to the Android source tree."""
from pathlib import Path
import subprocess
repo=Path('/root/t110-build/lineage20/frameworks/native')
patch=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/patches/0030-ui-t110-retained-gralloc-owners.patch')
base=['git','-C',str(repo),'apply']
already=subprocess.run(base+['--reverse','--check',str(patch)],capture_output=True).returncode==0
if not already:
    subprocess.run(base+['--check',str(patch)],check=True)
    subprocess.run(base+[str(patch)],check=True)
print('T110 retained-buffer patch already applied' if already else 'T110 retained-buffer patch applied')
