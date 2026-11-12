"""Derive an immutable v36 image and reversible block delta; change only netd."""
from pathlib import Path
import hashlib,json,os,re,shutil,struct,subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');b=Path('/root/t110-build');e=p/'evidence/hardware-v35/netd-event'
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
assert '[  PASSED  ] 8 tests.' in (e/'unit-tests.txt').read_text()
log=Path((e/'build-log.txt').read_text().strip());assert 'build completed successfully' in log.read_text(errors='replace')
parent=p/'artifacts/lineage20-rom-v35-gapps';a=p/'artifacts/lineage20-rom-v36-gapps';work=b/'export-lineage20-rom-v36-gapps'
assert not a.exists() and not work.exists()
old=json.loads((parent/'host-verification.json').read_text());base=parent/'system.raw.img'
def sha(f,kind='sha256'):
 with f.open('rb') as stream:return hashlib.file_digest(stream,kind).hexdigest()
assert sha(base)==old['sha256']=='e0233bc6685870d320ee5228f7323df6e76a28e62d106ab062a384cc03421ad3'
binary=b/'out-system/target/product/t110_bringup/system/bin/netd';payload=binary.read_bytes()
assert payload[:6]==b'\x7fELF\x01\x01' and struct.unpack_from('<H',payload,18)[0]==40
source=json.loads((e/'source.json').read_text())
for name,expected in source['files'].items():assert sha(b/'lineage20/system/netd'/name)==expected,name
work.mkdir();raw=work/'system.raw.img';shutil.copyfile(base,raw)
def debug(command,binary=False):
 r=subprocess.run(['debugfs','-R',command,str(raw)],capture_output=True,check=True)
 return r.stdout if binary else r.stdout.decode(errors='replace')
name='/system/bin/netd';before_stat=debug('stat '+name);before_attrs=debug('ea_list '+name)
assert 'Type: regular' in before_stat
mode=re.search(r'Mode:\s+([0-7]+)',before_stat)[1]
uid=re.search(r'User:\s+(\d+)',before_stat)[1];gid=re.search(r'Group:\s+(\d+)',before_stat)[1]
old_binary=debug('cat '+name,True);assert old_binary!=payload
xattrs=[]
for attribute,length in re.findall(r'^\s+([a-zA-Z0-9_.:-]+) \((\d+)\)',before_attrs,re.M):
 f=work/('xattr-'+str(len(xattrs))+'.bin');debug('ea_get -f '+str(f)+' '+name+' '+attribute)
 assert f.is_file() and f.stat().st_size==int(length),attribute
 xattrs.append((attribute,f))
assert any(attribute=='security.selinux' and f.read_bytes().rstrip(b'\0')==b'u:object_r:netd_exec:s0' for attribute,f in xattrs)
inode_mode=0o100000|int(mode,8)
commands=['rm '+name,'write '+str(binary)+' '+name,f'set_inode_field {name} mode 0{inode_mode:o}',f'set_inode_field {name} uid {uid}',f'set_inode_field {name} gid {gid}']
commands += ['ea_set -f '+str(f)+' '+name+' '+attribute for attribute,f in xattrs]
batch=work/'update.debugfs';batch.write_text('\n'.join(commands)+'\n')
r=subprocess.run(['debugfs','-w','-f',str(batch),str(raw)],capture_output=True,text=True);(work/'update.log').write_text(r.stdout+r.stderr);assert r.returncode==0
assert debug('cat '+name,True)==payload
after_stat=debug('stat '+name)
assert re.search(r'Mode:\s+([0-7]+)',after_stat)[1]==mode
assert re.search(r'User:\s+(\d+)',after_stat)[1]==uid and re.search(r'Group:\s+(\d+)',after_stat)[1]==gid
for attribute,f in xattrs:
 check=work/('check-'+f.name);debug('ea_get -f '+str(check)+' '+name+' '+attribute);assert check.read_bytes()==f.read_bytes()
for group in ('gapps_files','native_components_unchanged'):
 for filename,expected in old[group].items():assert hashlib.sha256(debug('cat /'+filename,True)).hexdigest()==expected,filename
ns={};exec((p/'scripts/verify_system_image_fit.py').read_text().split('if __name__',1)[0],ns)
fs=ns['inspect_ext4'](raw);assert fs['fsck_exit']==0 and fs['ext4_features']==old['ext4']['ext4_features']
a.mkdir();delta=a/'delta';delta.mkdir();ranges=[]
with base.open('rb',buffering=16*1024*1024) as before,raw.open('rb',buffering=16*1024*1024) as after:
 start=None;old_bytes=bytearray();new_bytes=bytearray();block=0
 def flush():
  if start is None:return
  number=len(ranges);forward=delta/f'{number:04d}.new.bin';reverse=delta/f'{number:04d}.old.bin'
  forward.write_bytes(new_bytes);reverse.write_bytes(old_bytes)
  ranges.append(dict(block=start,count=len(new_bytes)//4096,bytes=len(new_bytes),new_file=forward.name,old_file=reverse.name,
   new_sha256=sha(forward),old_sha256=sha(reverse)))
 while True:
  old_block=before.read(4096);new_block=after.read(4096);assert len(old_block)==len(new_block)
  if not old_block:flush();break
  if old_block!=new_block:
   if start is None:start=block
   old_bytes.extend(old_block);new_bytes.extend(new_block)
   if len(new_bytes)==1024*1024:flush();start=None;old_bytes=bytearray();new_bytes=bytearray()
  elif start is not None:flush();start=None;old_bytes=bytearray();new_bytes=bytearray()
  block+=1
assert ranges and sum(row['bytes'] for row in ranges)<8*1024*1024
record={**old,'status':'OFFLINE_VERIFIED_NOT_INSTALLED','parent_sha256':old['sha256'],'parent_md5':old['md5'],
 'sha256':sha(raw),'md5':sha(raw,'md5'),'ext4':fs,'updated_files':{'system/bin/netd':sha(binary)},
 'previous_netd_sha256':hashlib.sha256(old_binary).hexdigest(),'delta_block_size':4096,'delta_ranges':ranges,
 'delta_bytes':sum(row['bytes'] for row in ranges),'build_log':str(log),'netd_tests_passed':8,
 'system_image_required_boot':'android13-boot-v42','hardware_validated':False,'all_native_and_google_components_retained':True}
shutil.copyfile(raw,a/'system.raw.incoming');assert sha(a/'system.raw.incoming')==record['sha256'];(a/'system.raw.incoming').rename(a/'system.raw.img')
(a/'host-verification.json').write_text(json.dumps(record,indent=2)+'\n');print('V36_NETD_DELTA_VERIFIED',record['sha256'],'delta_bytes',record['delta_bytes'])
