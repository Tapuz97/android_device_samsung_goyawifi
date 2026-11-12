"""Prepare a reviewable source-only kernel checkpoint inside Ubuntu; no checkout/reset."""
from pathlib import Path
import subprocess,json,os
root=Path('/root/t110-build/kernel-display-i2c')
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
base='3c50b450af74d42f8c5d360c692f71002b3bb0af';branch='t110/android13-v42-checkpoint'
def git(*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
if not (root/'.git').exists():
 git('init');git('config','core.filemode','false');git('config','core.autocrlf','false')
 git('remote','add','origin','https://github.com/Tapuz97/android_kernel_samsung_goya.git')
 git('fetch','--filter=blob:none','--depth=1','origin',base)
 git('update-ref','refs/heads/'+branch,base);git('symbolic-ref','HEAD','refs/heads/'+branch)
 git('read-tree',base)
status=git('status','--porcelain','--untracked-files=normal')
(project/'community/kernel-checkpoint-status.txt').write_text(status+'\n')
print(status,flush=True)
print('SOURCE_REVIEW_READY',flush=True)
