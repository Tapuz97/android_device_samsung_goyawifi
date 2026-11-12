"""Fetch only the missing Lineage HAL interfaces at the build's pinned revision."""
from pathlib import Path
import subprocess,json
t=Path('/root/t110-build/lineage20');p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
dep=t/'hardware/lineage/interfaces';revision='56bf43755bdc4045ec56b4c02eaaaf9894f91003'
assert not dep.exists(),'Do not overwrite an existing checkout'
subprocess.run([str(t/'.repo/repo/repo'),'sync','-c','-j1','--no-tags','--no-clone-bundle','hardware/lineage/interfaces'],cwd=t,check=True,timeout=180)
head=subprocess.check_output(['git','-C',str(dep),'rev-parse','HEAD'],text=True).strip()
if head!=revision:
    assert not subprocess.check_output(['git','-C',str(dep),'status','--porcelain'])
    subprocess.run(['git','-C',str(dep),'fetch','--depth=1','origin',revision],check=True,timeout=120)
    subprocess.run(['git','-C',str(dep),'checkout','--detach',revision],check=True)
patch=p/'patches/0015-soong-binder32bit-android-only.patch'
data=patch.read_bytes()
subprocess.run(['git','-C',str(t/'build/soong'),'apply','--check','-'],input=data,check=True)
subprocess.run(['git','-C',str(t/'build/soong'),'apply','-'],input=data,check=True)
(p/'evidence/remote-fixes-20261110/sdk-dependencies.json').write_text(json.dumps({'only_fetched_project':'hardware/lineage/interfaces','revision':revision,'host_binder_patch':'0015','full_external_drive_environment':'still unavailable'},indent=2)+'\n')
print('PINNED_SDK_DEPENDENCY_READY')
