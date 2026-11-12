"""Linux metadata-preserving two-file update on a Windows-created private clone."""
from pathlib import Path
import hashlib,json,os,re,subprocess
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/hardware-bt-sd';a=p/'artifacts/lineage20-rom-v38-gapps';raw=a/'system.raw.incoming';work=Path('/root/t110-build/v38-bt-runpath');assert not work.exists();work.mkdir()
log=Path((e/'hal-runpath-build-log.txt').read_text().strip());assert 'build completed successfully' in log.read_text(errors='replace')
source=Path('/root/t110-build/out-system/target/product/t110_bringup/system/vendor/bin/hw/android.hardware.bluetooth@1.1-service')
elf=source.read_bytes();assert elf[:6]==b'\x7fELF\1\1'
tool='/root/t110-build/lineage20/prebuilts/clang/host/linux-x86/clang-r450784d/bin/llvm-readelf'
dynamic=subprocess.run([tool,'-d',str(source)],capture_output=True,text=True,check=True).stdout;assert 'RUNPATH' in dynamic and '/vendor/lib/hw' in dynamic
(e/'hal-runpath-elf.txt').write_text(dynamic)
rc=p/'work/device/samsung/t110_bringup/bluetooth/init.t110.bluetooth.rc';before=rc.read_bytes();old_source=json.loads((e/'device-source.json').read_text())
assert hashlib.sha256(before).hexdigest()==old_source['files']['bluetooth/init.t110.bluetooth.rc']
trigger=b'on property:init.svc.t110-radio-init=stopped\n    start t110-bluetooth-init\n\n';assert before.startswith(trigger)
corrected=before[len(trigger):];inputs={'system/vendor/bin/hw/android.hardware.bluetooth@1.1-service':elf,'system/vendor/etc/init/init.t110.bluetooth.rc':corrected}
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
batch=work/'update.debugfs';batch.write_text('\n'.join(commands)+'\n');r=subprocess.run(['debugfs','-w','-f',str(batch),str(raw)],capture_output=True,check=True);(e/'v38-update-debugfs.txt').write_bytes(r.stdout+r.stderr)
for name,data in inputs.items():
 path='/'+name;assert dbg('cat '+path,True)==data
 stat=dbg('stat '+path);mode,uid,gid,attributes=metadata[name]
 assert int(re.search(r'Mode:\s+([0-7]+)',stat)[1],8)==mode
 assert int(re.search(r'User:\s+(\d+)',stat)[1])==uid and int(re.search(r'Group:\s+(\d+)',stat)[1])==gid
 for key,f in attributes:
  check=work/'check-attr';dbg(f'ea_get -f {check} {path} {key}');assert check.read_bytes()==f.read_bytes()
candidate=work/'init.t110.bluetooth.rc';candidate.write_bytes(corrected)
verifier=subprocess.run(['/root/t110-build/out-system/host/linux-x86/bin/host_init_verifier',str(candidate)],capture_output=True);(e/'v38-vendor-init-verifier.txt').write_bytes(verifier.stdout+verifier.stderr);assert verifier.returncode==0
ns={};exec((p/'scripts/verify_system_image_fit.py').read_text().split('if __name__',1)[0],ns);fs=ns['inspect_ext4'](raw);assert fs['fsck_exit']==0
record=dict(updated_files={name:hashlib.sha256(data).hexdigest() for name,data in inputs.items()},ext4=fs,
 build_log=str(log),init_verifier_exit=0,embedded_runpath='/vendor/lib/hw',all_changed_file_metadata_and_attributes_retained=True,
 unchanged_payload_validation='Verified v37 clone; only the two listed regular-file contents were replaced. No package or directory deletion.')
(e/'v38-image-edit.json').write_text(json.dumps(record,indent=2)+'\n');(e/'hal-runpath-service').write_bytes(elf)
print('V38_TWO_FILE_UPDATE_METADATA_FSCK_INIT_AND_RUNPATH_PASS',flush=True)
