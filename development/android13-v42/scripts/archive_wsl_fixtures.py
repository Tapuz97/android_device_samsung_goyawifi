"""Preserve unique host test/build helpers in each distro, not rebuildable outputs."""
from pathlib import Path
import os,sys,tarfile,hashlib,json,subprocess
name=sys.argv[1];root=Path('/root/t110-build')
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
out=project/'backups/android13-before-lineage14-20261112';archive=out/(name+'-host-fixtures-private.tar.gz')
allowed={'.c','.cpp','.cc','.h','.S','.s','.py','.sh','.patch','.diff','.json','.md','.txt','.log','.cil','.te','.rc','.config','.mk','.xml','.map','.csv','.conf','.prop','.kl','.idc'}
skip=[];members=[]
def excluded(n):
 return n in {'lineage20','toolchain','stock-system-files','stock-radio-extract','android-common-3.4','kernel','kernel-display-i2c','os-manifest','private-search-preopt','ui-v40-search-preopt','ui-v41-search-preopt'} or n.startswith(('out-','export-','kernel-'))
with tarfile.open(archive,'w:gz',compresslevel=1) as t:
 for base,dirs,files in os.walk(root,followlinks=False):
  kept=[]
  for d in dirs:
   p=Path(base)/d
   if d in {'.git','.repo','__pycache__'} or p.is_symlink():continue
   if Path(base)==root and excluded(d):skip.append(d);continue
   kept.append(d)
  dirs[:]=kept
  for n in files:
   p=Path(base)/n
   if p.is_symlink() or p.stat().st_size>20*1024*1024:continue
   if p.suffix not in allowed and p.name not in {'Makefile','.config','SHA256SUMS','file_contexts'}:continue
   data=p.read_bytes()
   if b'\0' in data:continue
   rel=p.relative_to(root).as_posix();t.add(p,arcname=rel,recursive=False)
   members.append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 packages=subprocess.check_output(['dpkg-query','-W','-f=${Package} ${Version}\n'],text=True)
 pkg=out/(name+'-packages.txt');pkg.write_text(packages);t.add(pkg,arcname='RESTORE-HOST-PACKAGES.txt')
expected={x['path']:x for x in members}
with tarfile.open(archive,'r:gz') as t:
 for m in t:
  data=t.extractfile(m).read()
  if m.name in expected:
   item=expected.pop(m.name);assert hashlib.sha256(data).hexdigest()==item['sha256']
assert not expected
h=hashlib.sha256()
with archive.open('rb') as f:
 for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
result={'status':'HOST_FIXTURE_READBACK_PASS','distro':name,'archive':str(archive),'bytes':archive.stat().st_size,
 'sha256':h.hexdigest(),'members':members,'excluded_generated_or_separately_preserved_dirs':skip,
 'kernel_source_separately_archived':True,'current_lineage_source_delta_separately_archived':True}
(out/(name+'-host-fixtures.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='members'},indent=2),flush=True)
