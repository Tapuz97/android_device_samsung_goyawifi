"""Package the Search optimization as a verified reversible system-only update."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
observed='--runtime-paths' in sys.argv;version=41 if observed else 40
p=Path(__file__).resolve().parents[1];stage=p/'evidence/ui-system-hang-20261112'/('private-search-runtime-preopt' if observed else 'private-search-preopt')
manifest=json.loads((stage/'manifest.json').read_text());assert manifest['status']=='HOST_SEARCH_PREOPT_COMPILED_NOT_INSTALLED'
parent=p/f'artifacts/lineage20-rom-v{version-1}-gapps';a=p/f'artifacts/lineage20-rom-v{version}-gapps';base=parent/'system.raw.img'
def sha(f,kind='sha256'):
    with f.open('rb') as stream:return hashlib.file_digest(stream,kind).hexdigest()
old=json.loads((parent/'host-verification.json').read_text());assert sha(base)==old['sha256']
assert not a.exists(),'Inspect an existing candidate before rerunning the one-shot packager'
a.mkdir();raw=a/'system.raw.incoming';shutil.copyfile(base,raw);assert sha(raw)==old['sha256']
subprocess.run(['wsl.exe','-d','Ubuntu','--','python3','/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/scripts/patch_search_v40_image.py']+(['--runtime-paths'] if observed else []),check=True)
edit=json.loads((stage/'image-edit.json').read_text());assert edit['ext4']['ext4_features']==old['ext4']['ext4_features'] and raw.stat().st_size==base.stat().st_size
delta=a/'delta';delta.mkdir();ranges=[]
with base.open('rb',buffering=16*1024*1024) as before,raw.open('rb',buffering=16*1024*1024) as after:
    start=None;older=bytearray();newer=bytearray();block=0
    def flush():
        if start is None:return
        number=len(ranges);f=delta/f'{number:04d}.new.bin';r=delta/f'{number:04d}.old.bin';f.write_bytes(newer);r.write_bytes(older)
        ranges.append(dict(block=start,count=len(newer)//4096,bytes=len(newer),new_file=f.name,old_file=r.name,new_sha256=sha(f),old_sha256=sha(r)))
    while True:
        b=before.read(4096);c=after.read(4096);assert len(b)==len(c)
        if not b:flush();break
        if b!=c:
            if start is None:start=block
            older.extend(b);newer.extend(c)
            if len(newer)==1024*1024:flush();start=None;older=bytearray();newer=bytearray()
        elif start is not None:flush();start=None;older=bytearray();newer=bytearray()
        block+=1
assert ranges and sum(row['bytes'] for row in ranges)<220*1024*1024
record={**old,'status':'OFFLINE_VERIFIED_NOT_INSTALLED','parent_sha256':old['sha256'],'parent_md5':old['md5'],
        'sha256':sha(raw),'md5':sha(raw,'md5'),'updated_files':{**old['updated_files'],**edit['updated_files']},'ext4':edit['ext4'],
        'delta_ranges':ranges,'delta_bytes':sum(row['bytes'] for row in ranges),'delta_block_size':4096,
        'hardware_validated':False,'ui_fixed':False,'scoped_update_validation':edit,'build_log':str(stage/'host-compiler.log')}
if observed:
    bf=p/'artifacts/android13-boot-v47/provenance.json';boot=json.loads(bf.read_text());assert boot['standard_reclaim_enabled'] and boot['module_equivalence_verified']
    boot.update(status='OFFLINE_VERIFIED_NOT_INSTALLED',paired_system_sha256=record['sha256']);bf.write_text(json.dumps(boot,indent=2)+'\n')
    record.update(paired_boot_sha256=boot['full_boot_sha256'],system_image_required_boot='android13-boot-v47')
raw.rename(a/'system.raw.img');(a/'host-verification.json').write_text(json.dumps(record,indent=2)+'\n')
print(f'V{version}_SEARCH_PREOPT_OFFLINE_VERIFIED',record['sha256'],'delta_bytes',record['delta_bytes'],flush=True)
