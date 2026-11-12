"""Clone/hash/delta on the internal drive; avoid another full cross-WSL copy."""
from pathlib import Path
import hashlib,json,shutil,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';parent=p/'artifacts/lineage20-rom-v37-gapps';a=p/'artifacts/lineage20-rom-v38-gapps';assert not a.exists()
def sha(f,kind='sha256'):
 with f.open('rb') as s:return hashlib.file_digest(s,kind).hexdigest()
old=json.loads((parent/'host-verification.json').read_text());base=parent/'system.raw.img';assert sha(base)==old['sha256']
a.mkdir();raw=a/'system.raw.incoming';shutil.copyfile(base,raw);assert sha(raw)==old['sha256'];print('V37_PRIVATE_LOCAL_CLONE_VERIFIED',flush=True)
subprocess.run(['wsl.exe','-d','T110Build','--','python3','/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/scripts/patch_bt_v38_image.py'],check=True)
edit=json.loads((e/'v38-image-edit.json').read_text());assert edit['ext4']['ext4_features']==old['ext4']['ext4_features'] and raw.stat().st_size==base.stat().st_size
delta=a/'delta';delta.mkdir();ranges=[]
with base.open('rb',buffering=16*1024*1024) as before,raw.open('rb',buffering=16*1024*1024) as after:
 start=None;older=bytearray();newer=bytearray();block=0
 def flush():
  if start is None:return
  n=len(ranges);f=delta/f'{n:04d}.new.bin';r=delta/f'{n:04d}.old.bin';f.write_bytes(newer);r.write_bytes(older)
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
assert ranges and sum(row['bytes'] for row in ranges)<4*1024*1024
boot=json.loads((p/'artifacts/android13-boot-v44/provenance.json').read_text())
record={**old,'status':'OFFLINE_VERIFIED_NOT_INSTALLED','parent_sha256':old['sha256'],'parent_md5':old['md5'],
 'sha256':sha(raw),'md5':sha(raw,'md5'),'updated_files':{**old['updated_files'],**edit['updated_files']},'ext4':edit['ext4'],
 'native_components_unchanged':{key:edit['updated_files'].get(key,value) for key,value in old['native_components_unchanged'].items()},
 'delta_ranges':ranges,'delta_bytes':sum(row['bytes'] for row in ranges),'delta_block_size':4096,'build_log':edit['build_log'],
 'system_image_required_boot':'android13-boot-v45','paired_boot_sha256':None,'hardware_validated':False,'scoped_update_validation':edit}
raw.rename(a/'system.raw.img');(a/'host-verification.json').write_text(json.dumps(record,indent=2)+'\n')
print('V38_VERIFIED',record['sha256'],'delta_bytes',record['delta_bytes'],flush=True)
