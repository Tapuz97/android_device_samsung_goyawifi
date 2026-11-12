"""Derive a private reversible v37 update; retain all existing native/Google apps."""
from pathlib import Path
import hashlib,json,os,re,shutil,struct,subprocess
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');b=Path('/root/t110-build');e=p/'evidence/hardware-bt-sd';product=b/'out-system/target/product/t110_bringup'
parent=p/'artifacts/lineage20-rom-v36-gapps';a=p/'artifacts/lineage20-rom-v37-gapps';work=b/'export-lineage20-rom-v37-gapps';assert not a.exists() and not work.exists()
log=Path((e/'build-log.txt').read_text().strip());assert 'build completed successfully' in log.read_text(errors='replace')
tests=json.loads((e/'h4-unit-tests.json').read_text());assert tests['status']=='PASS' and tests['atomic_tests_passed']==2 and tests['legacy_tests_passed']>0
def sha(f,kind='sha256'):
 with f.open('rb') as stream:return hashlib.file_digest(stream,kind).hexdigest()
old=json.loads((parent/'host-verification.json').read_text());base=parent/'system.raw.img';assert sha(base)==old['sha256']=='a4cbd1d66d95d198587d7c898bb433bafd513567e41724ffe466d23fbca5f9cd'
for name,expected in json.loads((e/'h4-production-source.json').read_text())['files'].items():assert sha(b/'lineage20/hardware/interfaces'/name)==expected,name
for name,expected in json.loads((e/'device-source.json').read_text())['files'].items():assert sha(b/'lineage20/device/samsung/t110_bringup'/name)==expected,name
work.mkdir();source=work/'vanilla.raw.img';raw=work/'system.raw.img'
subprocess.run(['simg2img',str(product/'system.img'),str(source)],check=True);shutil.copyfile(base,raw)
def debug(image,command,binary=False):
 r=subprocess.run(['debugfs','-R',command,str(image)],capture_output=True,check=True)
 return r.stdout if binary else r.stdout.decode(errors='replace')
names=['system/build.prop','system/etc/linker.config.pb']
# Collect actual installed vendor files, including the HAL's normal dependencies.
# Existing byte-identical files are skipped; no parent file is deleted.
names.extend(str(f.relative_to(product)) for f in (product/'system/vendor').rglob('*') if f.is_file() and not f.is_symlink())
names.extend(str(f.relative_to(product)) for f in (product/'system/lib').rglob('*') if f.is_file() and not f.is_symlink())
preopt=list((product/'system/framework/oat/arm').glob('apex@com.android.btservices@app@Bluetooth@*@Bluetooth.apk@classes.odex'))
assert len(preopt)==1 and b'compiler-filter\x00speed\x00' in preopt[0].read_bytes(),'Bluetooth APEX speed precompile is required'
names.extend(str(f.relative_to(product)) for f in [preopt[0],preopt[0].with_suffix('.vdex')])
for directory in ['system/etc/selinux','system/vendor/etc/selinux','system/system_ext/etc/selinux','system/product/etc/selinux']:
 names.extend(str(f.relative_to(product)) for f in (product/directory).rglob('*') if f.is_file() and not f.is_symlink())
assert (product/'root/sepolicy').read_bytes()==(product/'system/vendor/etc/selinux/precompiled_sepolicy').read_bytes()
assert sha(product/'system/vendor/etc/bluetooth/modules/mbt8xxx.ko')==json.loads((e/'module-build.json').read_text())['module_sha256']
assert b'ro.bt.bdaddr_path=/data/vendor/t110-bluetooth/controller_address' in (product/'system/build.prop').read_bytes()
assert (product/'system/vendor/etc/fstab.mrvl').read_bytes()==(p/'work/device/samsung/t110_bringup/storage/fstab.mrvl').read_bytes()
commands=[];updated={};new_dirs=[];metadata={};counter=0
def inode_metadata(name,kind):
 global counter
 path='/'+name;info=debug(source,'stat '+path);assert ('Type: '+kind) in info,name
 mode=int(re.search(r'Mode:\s+([0-7]+)',info)[1],8)|(0o040000 if kind=='directory' else 0o100000)
 uid=int(re.search(r'User:\s+(\d+)',info)[1]);gid=int(re.search(r'Group:\s+(\d+)',info)[1])
 result=[f'set_inode_field {path} mode 0{mode:o}',f'set_inode_field {path} uid {uid}',f'set_inode_field {path} gid {gid}'];attrs=[]
 for attribute,length in re.findall(r'^\s+([A-Za-z0-9_.:-]+) \((\d+)\)',debug(source,'ea_list '+path),re.M):
  f=work/f'xattr-{counter:04d}.bin';counter+=1;debug(source,f'ea_get -f {f} {path} {attribute}')
  assert f.stat().st_size==int(length);result.append(f'ea_set -f {f} {path} {attribute}');attrs.append((attribute,f))
 assert any(key=='security.selinux' for key,_ in attrs),name
 metadata[name]=dict(mode=mode,uid=uid,gid=gid,attrs=attrs)
 return result
def ensure_directory(directory):
 name=directory.as_posix()
 if name in ('.','/'):return
 if name in new_dirs:return
 info=debug(raw,'stat /'+name)
 if info:assert 'Type: directory' in info,name;return
 ensure_directory(directory.parent);commands.append('mkdir /'+name);commands.extend(inode_metadata(name,'directory'));new_dirs.append(name)
for name in sorted(set(names)-old['gapps_files'].keys()):
 f=product/name;assert f.is_file() and not f.is_symlink(),name
 data=f.read_bytes();assert debug(source,'cat /'+name,True)==data,name
 before=debug(raw,'stat /'+name)
 if before and debug(raw,'cat /'+name,True)==data:continue
 if before:assert 'Type: regular' in before,name
 ensure_directory(Path(name).parent)
 if before:commands.append('rm /'+name)
 commands.append(f'write {f} /{name}');commands.extend(inode_metadata(name,'regular'));updated[name]=sha(f)
assert updated and 'system/vendor/bin/t110_bt_init' in updated
batch=work/'update.debugfs';batch.write_text('\n'.join(commands)+'\n')
r=subprocess.run(['debugfs','-w','-f',str(batch),str(raw)],capture_output=True,text=True);(work/'update.log').write_text(r.stdout+r.stderr);assert r.returncode==0
for name,expected in updated.items():assert hashlib.sha256(debug(raw,'cat /'+name,True)).hexdigest()==expected,name
for name,meta in metadata.items():
 info=debug(raw,'stat /'+name);assert int(re.search(r'Mode:\s+([0-7]+)',info)[1],8)==meta['mode']&0o7777,name
 assert int(re.search(r'User:\s+(\d+)',info)[1])==meta['uid'] and int(re.search(r'Group:\s+(\d+)',info)[1])==meta['gid'],name
 for attribute,f in meta['attrs']:
  check=work/('check-'+f.name);debug(raw,f'ea_get -f {check} /{name} {attribute}');assert check.read_bytes()==f.read_bytes(),name
for group in ['gapps_files','native_components_unchanged']:
 for name,expected in old[group].items():
  if group=='gapps_files':assert name not in updated,name
  assert hashlib.sha256(debug(raw,'cat /'+name,True)).hexdigest()==updated.get(name,expected),name
assert hashlib.sha256(debug(raw,'cat /system/bin/netd',True)).hexdigest()==old['updated_files']['system/bin/netd']
ns={};exec((p/'scripts/verify_system_image_fit.py').read_text().split('if __name__',1)[0],ns)
fs=ns['inspect_ext4'](raw);assert fs['fsck_exit']==0 and fs['ext4_features']==old['ext4']['ext4_features']
a.mkdir();delta=a/'delta';delta.mkdir();ranges=[]
with base.open('rb',buffering=16*1024*1024) as before,raw.open('rb',buffering=16*1024*1024) as after:
 start=None;old_bytes=bytearray();new_bytes=bytearray();block=0
 def flush():
  if start is None:return
  number=len(ranges);forward=delta/f'{number:04d}.new.bin';reverse=delta/f'{number:04d}.old.bin';forward.write_bytes(new_bytes);reverse.write_bytes(old_bytes)
  ranges.append(dict(block=start,count=len(new_bytes)//4096,bytes=len(new_bytes),new_file=forward.name,old_file=reverse.name,new_sha256=sha(forward),old_sha256=sha(reverse)))
 while True:
  old_block=before.read(4096);new_block=after.read(4096);assert len(old_block)==len(new_block)
  if not old_block:flush();break
  if old_block!=new_block:
   if start is None:start=block
   old_bytes.extend(old_block);new_bytes.extend(new_block)
   if len(new_bytes)==1024*1024:flush();start=None;old_bytes=bytearray();new_bytes=bytearray()
  elif start is not None:flush();start=None;old_bytes=bytearray();new_bytes=bytearray()
  block+=1
assert ranges and sum(row['bytes'] for row in ranges)<128*1024*1024
record={**old,'status':'OFFLINE_VERIFIED_NOT_INSTALLED','parent_sha256':old['sha256'],'parent_md5':old['md5'],
 'sha256':sha(raw),'md5':sha(raw,'md5'),'ext4':fs,'updated_files':{**old['updated_files'],**updated},
 'native_components_unchanged':{name:updated.get(name,value) for name,value in old['native_components_unchanged'].items()},
 'bootstrap_policy_sha256':sha(product/'root/sepolicy'),'delta_block_size':4096,'delta_ranges':ranges,'delta_bytes':sum(row['bytes'] for row in ranges),
 'build_log':str(log),'system_image_required_boot':'android13-boot-v43','hardware_validated':False,'all_native_and_google_components_retained':True,
 'bluetooth_qualified_stage':'controller transport and Wi-Fi coexistence; native stack pending','microSD_physical_test':'PENDING','new_directories':new_dirs}
shutil.copyfile(raw,a/'system.raw.incoming');assert sha(a/'system.raw.incoming')==record['sha256'];(a/'system.raw.incoming').rename(a/'system.raw.img')
(a/'host-verification.json').write_text(json.dumps(record,indent=2)+'\n')
(e/'sepolicy').write_bytes((product/'root/sepolicy').read_bytes())
print('V37_BLUETOOTH_SD_IMAGE_VERIFIED',record['sha256'],'delta_bytes',record['delta_bytes'])
