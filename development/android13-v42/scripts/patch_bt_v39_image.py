"""Preserve metadata while installing the loader and Bluetooth watchdog fixes."""
from pathlib import Path
import hashlib,json,os,re,subprocess
assert os.environ.get('WSL_DISTRO_NAME') in ('T110Build','Ubuntu')
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/hardware-bt-sd';a=p/'artifacts/lineage20-rom-v39-gapps';raw=a/'system.raw.incoming';work=Path('/root/t110-build/v39-bt-identity-watchdog')
if work.exists():assert work.is_dir() and not list(work.iterdir()),'Inspect an incomplete image edit before resuming'
else:work.mkdir()
stage=e/'v39-components';staged=json.loads((stage/'manifest.json').read_text());assert staged['status']=='NATIVE_COMPONENTS_EXPORTED_VERIFIED'
log=Path(staged['build_log']);saved_log=(stage/'native-build.log').read_bytes()
assert hashlib.sha256(saved_log).hexdigest()==staged['saved_build_log_sha256'] and b'build completed successfully' in saved_log and b'\0' not in saved_log
guard=json.loads((e/'lookup-watchdog-source.json').read_text());assert guard['actual_guard_lambda_test']['after']==0 and guard['watchdog_milliseconds_unchanged']==500
assert staged['watchdog_source']['after_sha256']==guard['after_sha256']
ledger=json.loads((e/'device-source.json').read_text());source=p/'work/device/samsung/t110_bringup/bluetooth/t110_bt_init.c'
assert staged['device_source']['files']['bluetooth/t110_bt_init.c']==ledger['files']['bluetooth/t110_bt_init.c']
assert hashlib.sha256(source.read_bytes()).hexdigest()==ledger['files']['bluetooth/t110_bt_init.c'] and b'fchmod(out,0640)==0' in source.read_bytes()
names=['system/vendor/bin/t110_bt_init','system/apex/com.android.btservices/lib/libbluetooth_jni.so'];assert set(staged['files'])==set(names)
inputs={}
for i,name in enumerate(names):
 entry=staged['files'][name];assert entry['file']==f'component-{i}.elf';f=stage/entry['file'];assert f.is_file() and not f.is_symlink()
 data=f.read_bytes();assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256'];inputs[name]=data
assert all(data[:6]==b'\x7fELF\1\1' for data in inputs.values()) and b'fchmod\0' in inputs[names[0]]
assert b'Unable to get a Bluetooth service after 500ms' in inputs[names[1]]
def dbg(command,binary=False):
 r=subprocess.run(['debugfs','-R',command,str(raw)],capture_output=True,check=True)
 return r.stdout if binary else r.stdout.decode(errors='replace')
commands=[];metadata={}
for number,(name,data) in enumerate(inputs.items()):
 path='/'+name;stat=dbg('stat '+path);assert 'Type: regular' in stat,name
 mode=int(re.search(r'Mode:\s+([0-7]+)',stat)[1],8);uid=int(re.search(r'User:\s+(\d+)',stat)[1]);gid=int(re.search(r'Group:\s+(\d+)',stat)[1]);attributes=[]
 for key,length in re.findall(r'^\s+([A-Za-z0-9_.:-]+) \((\d+)\)',dbg('ea_list '+path),re.M):
  f=work/f'attr-{number}-{len(attributes)}';dbg(f'ea_get -f {f} {path} {key}');assert f.stat().st_size==int(length);attributes.append((key,f))
 assert any(key=='security.selinux' for key,_ in attributes)
 f=work/f'payload-{number}';f.write_bytes(data)
 commands.extend(['rm '+path,f'write {f} {path}',f'set_inode_field {path} mode 0{mode|0o100000:o}',f'set_inode_field {path} uid {uid}',f'set_inode_field {path} gid {gid}'])
 for key,f in attributes:commands.append(f'ea_set -f {f} {path} {key}')
 metadata[name]=(mode,uid,gid,attributes)
batch=work/'update.debugfs';batch.write_text('\n'.join(commands)+'\n');r=subprocess.run(['debugfs','-w','-f',str(batch),str(raw)],capture_output=True,check=True);(e/'v39-update-debugfs.txt').write_bytes(r.stdout+r.stderr)
for name,data in inputs.items():
 path='/'+name;assert dbg('cat '+path,True)==data
 stat=dbg('stat '+path);mode,uid,gid,attributes=metadata[name]
 assert int(re.search(r'Mode:\s+([0-7]+)',stat)[1],8)==mode and int(re.search(r'User:\s+(\d+)',stat)[1])==uid and int(re.search(r'Group:\s+(\d+)',stat)[1])==gid
 for key,f in attributes:
  check=work/'check-attr';dbg(f'ea_get -f {check} {path} {key}');assert check.read_bytes()==f.read_bytes()
ns={};exec((p/'scripts/verify_system_image_fit.py').read_text().split('if __name__',1)[0],ns);fs=ns['inspect_ext4'](raw);assert fs['fsck_exit']==0
record=dict(updated_files={name:hashlib.sha256(data).hexdigest() for name,data in inputs.items()},ext4=fs,build_log=str(log),
 all_changed_file_metadata_and_attributes_retained=True,identity_file_fchmod=True,lookup_watchdog_source=guard,
 unchanged_payload_validation='Verified v38 clone; only the two listed regular-file contents replaced. No APK, package, permission or directory deletion.')
(e/'v39-image-edit.json').write_text(json.dumps(record,indent=2)+'\n');print('V39_LOADER_AND_WATCHDOG_IMAGE_FSCK_AND_METADATA_PASS',flush=True)
