"""Apply the audited cumulative v21 source patches; no tablet access."""
from pathlib import Path
import subprocess
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
root=Path('/root/t110-build/lineage20')
for repo, name in [
    ('hardware/interfaces','0033-composer-t110-direct-fb-scanout.patch'),
    ('frameworks/native','0034-ui-t110-linear-scanout-targets.patch')]:
    patch=project/'patches'/name
    cwd=root/repo
    if subprocess.run(['git','apply','--reverse','--check',str(patch)],cwd=cwd,capture_output=True).returncode==0:
        print('Already applied:',name)
        continue
    subprocess.run(['git','apply','--check',str(patch)],cwd=cwd,check=True)
    subprocess.run(['git','apply',str(patch)],cwd=cwd,check=True)
