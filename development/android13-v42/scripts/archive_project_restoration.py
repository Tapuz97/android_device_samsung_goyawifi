"""Private restoration set, streamed into release-sized pieces; never deletes originals."""
from pathlib import Path
import os,io,tarfile,hashlib,json
r=Path(__file__).resolve().parents[1];out=r/'backups/android13-before-lineage14-20261112'
limit=1792*1024*1024
class Parts(io.RawIOBase):
 def __init__(self):self.f=None;self.index=0;self.used=0;self.paths=[]
 def writable(self):return True
 def write(self,data):
  original=len(data)
  while data:
   if self.f is None:
    p=out/('project-restoration-private.tar.gz.part%03d'%self.index)
    assert not p.exists(),('Existing archive part; do not overwrite',p)
    self.paths.append(p);self.f=p.open('wb');self.used=0;self.index+=1
   size=min(len(data),limit-self.used);self.f.write(data[:size]);data=data[size:];self.used+=size
   if self.used==limit:self.f.close();self.f=None
  return original
 def finish(self):
  if self.f:self.f.close();self.f=None
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
excluded_prefixes=['backups/android13-before-lineage14-20261112/','community/device-checkpoint/','community/gerrit-soong/']
excluded_files={'artifacts/lineage20-rom-v42-gapps/system.raw.img','artifacts/android13-boot-v48/KERNEL.img',
 'firmware/CODE_T110XXUANI7_2751957_REV02_user_low_ship.tar.md5','firmware/extracted/system.img.sparse'}
retired=json.loads((r/'cleanup/lineage14-pivot/retirement-inventory.json').read_text())
obsolete={x['name'] for x in retired}
members=[];skipped=[];links=[]
writer=Parts()
with tarfile.open(fileobj=writer,mode='w|gz',compresslevel=1) as archive:
 for base,dirs,files in os.walk(r,followlinks=False):
  kept=[]
  for name in dirs:
   p=Path(base)/name;rel=p.relative_to(r).as_posix()
   if name in {'.git','__pycache__','venv'} or any((rel+'/').startswith(x) for x in excluded_prefixes):continue
   if p.is_symlink() or os.path.isjunction(p):links.append({'path':rel,'target':str(p.resolve())});continue
   if len(p.relative_to(r).parts)==2 and p.parent.name=='artifacts' and name in obsolete:continue
   kept.append(name)
  dirs[:]=kept
  for name in files:
   p=Path(base)/name;rel=p.relative_to(r).as_posix()
   if p.is_symlink():links.append({'path':rel,'target':str(p.resolve())});continue
   if rel in excluded_files:
    skipped.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)});continue
   item={'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)}
   archive.add(p,arcname='SM-T110/'+rel,recursive=False);members.append(item)
   if len(members)%1000==0:print('ARCHIVED_FILES',len(members),flush=True)
writer.finish()
parts=[{'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in writer.paths]
manifest={'members':members,'parts':parts,'excluded_redundant_files':skipped,'external_links_not_followed':links,
 'excluded_obsolete_artifact_directories':sorted(obsolete),'exclusions_explained':[
 'The v42 system and BOOT48 are in android13-current-private.tar.gz.',
 'Stock CODE tar and sparse system are extracted outputs of the retained firmware ZIP.',
 'The three new private source/current archives are separate release assets.',
 'Versioned obsolete outputs are superseded; their original metadata and conclusions are retained.',
 'Git upstream clones, installed pip caches and compiled objects are reproducible dependencies, not unique work.',
 'Junctions pointing to D or elsewhere are only recorded; no outside volume is traversed.']}
(out/'project-restoration-members.json').write_text(json.dumps(manifest,indent=2)+'\n')
class Joined(io.RawIOBase):
 def __init__(self,paths):self.paths=iter(paths);self.f=None
 def readable(self):return True
 def read(self,n=-1):
  if n<0:n=1024*1024
  chunks=[];remaining=n
  while remaining:
   if self.f is None:
    try:self.f=next(self.paths).open('rb')
    except StopIteration:break
   b=self.f.read(remaining)
   if b:chunks.append(b);remaining-=len(b)
   else:self.f.close();self.f=None
  return b''.join(chunks)
expected={'SM-T110/'+x['path']:x for x in members};count=0
with tarfile.open(fileobj=Joined(writer.paths),mode='r|gz') as archive:
 for member in archive:
  item=expected.pop(member.name);f=archive.extractfile(member);h=hashlib.sha256()
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
  assert item['sha256']==h.hexdigest() and item['bytes']==member.size,member.name
  count+=1
assert not expected
result={'status':'ALL_RESTORATION_MEMBERS_HASH_VERIFIED','members':count,'parts':parts,
 'online_uploaded':False,'source_or_original_deleted':False,'private':True}
(out/'project-restoration-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
