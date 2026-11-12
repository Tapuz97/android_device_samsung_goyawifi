"""Capture the final records/operator source, after payload and derivation checks."""
from pathlib import Path
import tarfile,json,hashlib
r=Path(__file__).resolve().parents[1];out=r/'backups/android13-before-lineage14-20261112'
state=json.loads((out/'online-backup-verification.json').read_text())
assert len(state['assets'])==8 and all(x['download_sha256_verified'] for x in state['assets'].values())
assert json.loads((out/'project-restoration-verification.json').read_text())['status']=='ALL_RESTORATION_MEMBERS_HASH_VERIFIED'
assert json.loads((out/'firmware-derivation-verified.json').read_text())['status']=='EXCLUDED_EXTRACTIONS_REPRODUCIBLE'
assert json.loads((out/'changed-project-bases-online.json').read_text())['count']==25
files=set(r.glob('*.md'))|set(r.glob('*.json'))
for folder in ['scripts','evidence/lineage14-audit','cleanup/lineage14-pivot']:
 for p in (r/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and not p.is_symlink():files.add(p)
for p in (r/'community').iterdir():
 if p.is_file() and p.suffix in {'.json','.md','.txt'}:files.add(p)
for p in out.iterdir():
 if p.is_file() and p.suffix in {'.json','.txt','.bundle'}:files.add(p)
for p in (out/'lineage20-source-delta').rglob('*'):
 if p.is_file():files.add(p)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
archive=out/'final-metadata-private.tar.gz';assert not archive.exists()
members=[]
with tarfile.open(archive,'w:gz',compresslevel=1) as t:
 for p in sorted(files):
  item={'path':p.relative_to(r).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
  t.add(p,arcname='SM-T110/'+item['path'],recursive=False);members.append(item)
expected={'SM-T110/'+x['path']:x for x in members}
with tarfile.open(archive,'r:gz') as t:
 for m in t:
  item=expected.pop(m.name);h=hashlib.sha256();f=t.extractfile(m)
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
  assert h.hexdigest()==item['sha256'] and len(members)>0,m.name
assert not expected
result={'status':'FINAL_METADATA_ALL_MEMBERS_HASH_VERIFIED','archive':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'members':members,
 'device_source':json.loads((r/'community/source-checkpoint-publication.json').read_text()),
 'kernel_source':json.loads((r/'community/kernel-checkpoint-commit.json').read_text())}
(out/'final-metadata-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='members'},indent=2),flush=True)
