"""Run inside the named WSL distro. Private source checkpoint, no build/write to tablet."""
from pathlib import Path
import subprocess, json, tarfile, hashlib, sys, os, concurrent.futures

mode=sys.argv[1]
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
out=project/'backups/android13-before-lineage14-20261112'
def run(args,cwd=None):
    return subprocess.check_output(args,cwd=cwd,stderr=subprocess.PIPE,timeout=90)
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
if mode=='lineage':
    root=Path('/root/t110-build/lineage20')
    stage=out/'lineage20-source-delta';stage.mkdir(exist_ok=True)
    run(['python3',str(root/'.repo/repo/repo'),'manifest','-r','-o',str(stage/'pinned-manifest.xml')],root)
    projects=(root/'.repo/project.list').read_text().splitlines()
    def export(rel):
        p=root/rel
        if not p.exists():return {'path':rel,'missing':True}
        head=run(['git','rev-parse','HEAD'],p).decode().strip()
        diff=run(['git','diff','--binary','HEAD','--'],p)
        untracked=run(['git','ls-files','--others','--exclude-standard','-z'],p).split(b'\0')
        untracked=[os.fsdecode(x) for x in untracked if x]
        if diff:
            target=stage/'patches'/(rel+'.patch');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(diff)
        return {'path':rel,'head':head,'diff_bytes':len(diff),'untracked':untracked}
    records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for i,item in enumerate(pool.map(export,projects)):
            records.append(item)
            if i%100==0: print('PROJECTS',i,'of',len(projects),flush=True)
    (stage/'projects.json').write_text(json.dumps(records,indent=2)+'\n')
    archive=out/'lineage20-source-delta-private.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=1) as t:
        t.add(stage,arcname='source-delta')
        for item in records:
            for rel in item.get('untracked',[]):
                p=root/item['path']/rel
                assert p.is_file() or p.is_symlink(),p
                assert p.stat().st_size<100*1024*1024,('Unexpected large untracked file',p)
                t.add(p,arcname='untracked/'+item['path']+'/'+rel,recursive=False)
        # This custom product is outside repo-managed projects.
        t.add(root/'device/samsung/t110_bringup',arcname='custom-product/t110_bringup')
        t.add(root/'.repo/manifests',arcname='manifest-source',filter=lambda x:None if '/.git' in x.name else x)
    info={'mode':mode,'projects':len(records),'dirty_projects':sum(bool(x.get('diff_bytes') or x.get('untracked')) for x in records),
          'missing_projects':[x['path'] for x in records if x.get('missing')], 'custom_product_included':True}
elif mode=='kernel':
    root=Path('/root/t110-build/kernel-display-i2c')
    archive=out/'kernel-source-private.tar.gz'
    exclusions={'.git','__pycache__'}
    def filt(item):
        bits=Path(item.name).parts
        if any(x in exclusions for x in bits):return None
        if item.name.endswith(('.o','.a','.cmd','.d','.tmp')):return None
        return item
    with tarfile.open(archive,'w:gz',compresslevel=1) as t:
        t.add(root,arcname='kernel-display-i2c',filter=filt)
        for rel in ['.config','Module.symvers','modules.order']:
            p=Path('/root/t110-build/out-standard-reclaim')/rel
            if p.exists():t.add(p,arcname='tested-config/'+rel)
    info={'mode':mode,'full_kernel_source':True,'generated_objects_excluded':True}
else:raise ValueError(mode)
# Decompress every member to force gzip integrity verification, without extraction.
count=0
with tarfile.open(archive,'r:gz') as t:
    for member in t:
        f=t.extractfile(member) if member.isfile() else None
        if f:
            while f.read(8*1024*1024):pass
        count+=1
info.update(archive=str(archive),bytes=archive.stat().st_size,sha256=digest(archive),members=count,status='ARCHIVE_READBACK_PASS')
(out/(mode+'-source-export.json')).write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(info,indent=2),flush=True)
