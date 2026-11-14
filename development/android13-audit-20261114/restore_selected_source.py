"""Restore pinned, changed Android13 files only; never create a full build/output tree."""
from pathlib import Path
import subprocess,json,re,urllib.request,concurrent.futures,shutil,hashlib
root=Path('/root/t110-android13-audit')
restored=root/'restored'
records={x['path']:x for x in json.loads((restored/'source-delta/projects.json').read_text())}
projects={'frameworks/native':'LineageOS/android_frameworks_native','hardware/interfaces':'LineageOS/android_hardware_interfaces'}
extras={'frameworks/native':['libs/gui/Surface.cpp'], 'hardware/interfaces':[
'audio/core/all-versions/default/Device.cpp','audio/core/all-versions/default/StreamIn.cpp',
'audio/core/all-versions/default/StreamOut.cpp','audio/core/all-versions/default/DevicesFactory.cpp']}
provenance=[]
for project,repo in projects.items():
    dest=root/'platform'/project;dest.mkdir(parents=True,exist_ok=True)
    patch=restored/'source-delta/patches'/str(project+'.patch')
    text=patch.read_text()
    files=set(re.findall(r'^--- a/(.+)$',text,re.M))|set(extras[project])
    def fetch(name):
        url='https://raw.githubusercontent.com/'+repo+'/'+records[project]['head']+'/'+name
        data=urllib.request.urlopen(url,timeout=60).read()
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        return dict(project=project,path=name,url=url,sha256=hashlib.sha256(data).hexdigest())
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        provenance.extend(pool.map(fetch,sorted(files)))
    subprocess.run(['git','init','-q',str(dest)],check=True)
    subprocess.run(['git','-C',str(dest),'add','.'],check=True)
    subprocess.run(['git','-C',str(dest),'-c','user.name=T110 audit','-c','user.email=audit@localhost','commit','-qm','Pinned upstream subset '+records[project]['head']],check=True)
    subprocess.run(['git','-C',str(dest),'apply','--check',str(patch)],check=True)
    subprocess.run(['git','-C',str(dest),'apply',str(patch)],check=True)
    untracked=restored/'untracked'/project
    if untracked.exists():shutil.copytree(untracked,dest,dirs_exist_ok=True)
    subprocess.run(['git','-C',str(dest),'add','.'],check=True)
    subprocess.run(['git','-C',str(dest),'-c','user.name=T110 audit','-c','user.email=audit@localhost','commit','-qm','Restored exact Android13 checkpoint patches'],check=True)
    print('Restored',project,len(files),'pinned upstream files plus checkpoint changes.',flush=True)
(root/'upstream-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
