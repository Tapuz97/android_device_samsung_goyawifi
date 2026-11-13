"""Preserve pinned upstream revisions, exact patches and newly authored source."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

BASE=Path('/root/t110-lineage14')
ANDROID=BASE/'android'
DEST=BASE/'records/source'
DEST.mkdir(parents=True,exist_ok=True)
projects=['bionic','frameworks/native','hardware/libhardware','frameworks/base',
          'system/core','packages/apps/CMParts','frameworks/av',
          'system/vold','packages/apps/Camera2','system/netd','packages/apps/Recorder']
records=[]
for name in projects:
    repo=ANDROID/name
    head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    patch=subprocess.check_output(['git','-C',str(repo),'diff','--binary','--full-index','HEAD'])
    target=DEST/(name.replace('/','__')+'.patch');target.write_bytes(patch)
    subprocess.run(['git','-C',str(repo),'diff','--check'],check=True)
    files=[]
    paths=subprocess.check_output(['git','-C',str(repo),'ls-files','--others','--exclude-standard','-z'])
    for raw in paths.split(b'\0'):
        if not raw:continue
        relative=raw.decode();source=repo/relative
        if source.is_file():
            output=DEST/'untracked'/name/relative
            output.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,output)
            files.append({'path':relative,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    records.append({'project':name,'head':head,'patch':target.name,
                    'patch_sha256':hashlib.sha256(patch).hexdigest(),'untracked':files})
(DEST/'projects.json').write_text(json.dumps(records,indent=2)+'\n')
subprocess.run(['repo','manifest','-r','-o',str(DEST/'pinned-manifest.xml')],cwd=ANDROID,check=True)
# Device source is separate from repo's upstream project set. Never export private blobs.
device=ANDROID/'device/samsung/goyawifi'
for source in device.rglob('*'):
    relative=source.relative_to(device)
    if any(part in ('.git','proprietary','prebuilt') for part in relative.parts):continue
    if not source.is_file() or source.suffix=='.json':continue
    output=DEST/'device/samsung/goyawifi'/relative
    output.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,output)
print('Preserved %d project diffs, all new source, device configuration and pinned manifest.' % len(projects))
