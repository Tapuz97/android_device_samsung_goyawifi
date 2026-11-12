"""Fill explicitly named missing projects; never update an existing source checkout."""
from pathlib import Path
import subprocess,sys,xml.etree.ElementTree as ET,json
t=Path('/root/t110-build/lineage20');p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
projects={x.get('path',x.get('name')):x for x in ET.parse(p/'evidence/lineage20-full-manifest-pinned.xml').iter('project')}
paths=sys.argv[1:];assert paths and len(paths)<10
for path in paths:
    assert path in projects and not(t/path).exists(),path
subprocess.run([str(t/'.repo/repo/repo'),'sync','-c','-j1','--no-tags','--no-clone-bundle',*paths],cwd=t,check=True,timeout=300)
record={}
for path in paths:
    dep=t/path;revision=projects[path].get('revision');assert revision and len(revision)==40
    assert not subprocess.check_output(['git','-C',str(dep),'status','--porcelain'])
    head=subprocess.check_output(['git','-C',str(dep),'rev-parse','HEAD'],text=True).strip()
    if head!=revision:
        # Resolve the existing manifest remote rather than assuming its name.
        remote=subprocess.check_output(['git','-C',str(dep),'remote'],text=True).split()[0]
        subprocess.run(['git','-C',str(dep),'fetch','--depth=1',remote,revision],check=True,timeout=180)
        subprocess.run(['git','-C',str(dep),'checkout','--detach',revision],check=True)
    record[path]=revision
out=p/'evidence/remote-fixes-20261110/internal-added-projects.json'
previous=json.loads(out.read_text()) if out.exists() else {};previous.update(record)
out.write_text(json.dumps(previous,indent=2)+'\n');print(json.dumps(record,indent=2))
