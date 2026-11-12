"""Private checkpoint and conservative generated-output retirement inventory.

Never follows junctions, deletes files, touches tablet partitions or publishes blobs.
"""
from pathlib import Path
import os, hashlib, json, tarfile, shutil, re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'backups/android13-before-lineage14-20261112'
OUT.mkdir(parents=True, exist_ok=True)

def walk(root):
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}
                   and not os.path.islink(Path(base)/d) and not os.path.isjunction(Path(base)/d)]
        for name in files:
            p = Path(base)/name
            if not p.is_symlink():
                yield p

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024), b''): h.update(b)
    return h.hexdigest()

images = {
 'artifacts/lineage20-rom-v42-gapps/system.raw.img':'aac99e674a85bc94dab1f794e81501a35c2b3958188a2f0a985717a5ddbeeb16',
 'artifacts/android13-boot-v48/KERNEL.img':'09da369cd22d09e1b59b70ce273fa305c96cc83bc83bca8a48132737763d3690',
 'artifacts/lineage20-rom-v41-gapps/system.raw.img':'a4e11ac1a749ae31f43118d1a0080a0dff7290ed30e2a3b0583467e4a03e114f',
 'artifacts/android13-boot-v47/KERNEL.img':'553f292654a703cb259c3e77bd77370e1c6b968f13e86ce886b3d4caa8e2b085',
}
verified=[]
for rel,expected in images.items():
    p=ROOT/rel
    actual=sha(p)
    assert actual==expected, (rel, actual)
    verified.append(dict(path=rel,bytes=p.stat().st_size,sha256=actual))
    print('VERIFIED',rel,flush=True)

files=set(ROOT.glob('*.md')) | set(ROOT.glob('*.json'))
for folder in ['work','patches','scripts','community','cleanup']:
    files.update(walk(ROOT/folder))
for rel in ['evidence/ui-system-hang-20261112/standard-reclaim-components',
            'evidence/ui-system-hang-20261112/v42-persistence',
            'evidence/v42-owner-unresponsive']:
    files.update(walk(ROOT/rel))
for p in (ROOT/'evidence/ui-system-hang-20261112').glob('*'):
    if p.is_file() and p.suffix in {'.json','.config','.patch','.md','.py','.txt'}:files.add(p)
files.update(ROOT/x for x in images if 'v42-' in x or 'v48/' in x)
archive=OUT/'android13-current-private.tar.gz'
manifest=[]
if not archive.exists():
    with tarfile.open(archive.with_suffix('.partial'),'w:gz',compresslevel=1) as t:
        for p in sorted(files):
            if not p.is_file():continue
            rel=p.relative_to(ROOT).as_posix()
            digest=sha(p)
            t.add(p,arcname=rel,recursive=False)
            manifest.append(dict(path=rel,bytes=p.stat().st_size,sha256=digest))
    archive.with_suffix('.partial').replace(archive)
    (OUT/'members.json').write_text(json.dumps(manifest,indent=2)+'\n')
else:
    manifest=json.loads((OUT/'members.json').read_text())
expected={x['path']:x for x in manifest}
with tarfile.open(archive,'r:gz') as t:
    for member in t:
        item=expected.pop(member.name)
        h=hashlib.sha256()
        f=t.extractfile(member)
        for b in iter(lambda:f.read(8*1024*1024), b''):h.update(b)
        assert h.hexdigest()==item['sha256'] and member.size==item['bytes'],member.name
assert not expected
result=dict(status='LOCAL_IMAGES_AND_SOURCE_ARCHIVE_VERIFIED',archive=str(archive),
 archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,members=len(manifest),
 verified_images=verified,full_source_export='PENDING_E_AND_UBUNTU_EXPORT',
 private=True,published=False,free_c_bytes=shutil.disk_usage(ROOT).free)
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)

retired=[]
for directory in sorted((ROOT/'artifacts').iterdir()):
    if not directory.is_dir() or directory.is_symlink() or os.path.isjunction(directory):continue
    n=directory.name
    obsolete=(re.fullmatch(r'lineage20-rom-v\d+(?:-gapps)?',n) and n not in {'lineage20-rom-v41-gapps','lineage20-rom-v42-gapps'}) or (re.fullmatch(r'android13-(?:boot|full|core|ramdisk)-v\d+',n) and n not in {'android13-boot-v47','android13-boot-v48'})
    if not obsolete:continue
    listing=[];metadata={}
    for p in walk(directory):
        rel=p.relative_to(directory).as_posix()
        listing.append(dict(path=rel,bytes=p.stat().st_size))
        if p.suffix in {'.json','.md','.config','.txt'} and p.stat().st_size<2*1024*1024:
            metadata[rel]=p.read_text(errors='replace')
    retired.append(dict(path=str(directory.resolve()),name=n,bytes=sum(x['bytes'] for x in listing),files=listing,metadata=metadata))
dest=ROOT/'cleanup/lineage14-pivot'
dest.mkdir(exist_ok=True)
(dest/'retirement-inventory.json').write_text(json.dumps(retired,indent=2)+'\n')
print('RETIREMENT_READY',len(retired),sum(x['bytes'] for x in retired),flush=True)
