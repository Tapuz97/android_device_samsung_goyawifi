"""Replace only verified policy files, retaining the v41 APKs and hardware payload."""
from pathlib import Path
import hashlib,json,os,re,subprocess
assert os.environ.get('WSL_DISTRO_NAME')=='Ubuntu'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/ui-system-hang-20261112'
stage=e/'reclaim-policy-components';meta=json.loads((stage/'manifest.json').read_text());assert meta['status']=='STANDARD_POLICY_COMPILED_EXPORTED'
raw=p/'artifacts/lineage20-rom-v42-gapps/system.raw.incoming';work=Path('/root/t110-build/v42-persistent-policy');assert not work.exists();work.mkdir()
sha=lambda data:hashlib.sha256(data).hexdigest()
def dbg(command,binary=False):
 r=subprocess.run(['debugfs','-R',command,str(raw)],capture_output=True,check=True)
 return r.stdout if binary else r.stdout.decode(errors='replace')
commands=[];updated={};metadata={}
for name,entry in meta['files'].items():
 assert name.startswith(('system/etc/selinux/','system/vendor/etc/selinux/','system/system_ext/etc/selinux/','system/product/etc/selinux/'))
 source=stage/entry['file'];data=source.read_bytes();assert len(data)==entry['bytes'] and sha(data)==entry['sha256']
 path='/'+name;stat=dbg('stat '+path)
 assert 'Type: regular' in stat,('Unexpected new policy file; inspect before adding',name)
 if dbg('cat '+path,True)==data:continue
 mode=int(re.search(r'Mode:\s+([0-7]+)',stat)[1],8);uid=int(re.search(r'User:\s+(\d+)',stat)[1]);gid=int(re.search(r'Group:\s+(\d+)',stat)[1]);attrs=[]
 for key,length in re.findall(r'^\s+([A-Za-z0-9_.:-]+) \((\d+)\)',dbg('ea_list '+path),re.M):
  attr=work/f'attr-{len(updated)}-{len(attrs)}';dbg(f'ea_get -f {attr} {path} {key}');assert attr.stat().st_size==int(length);attrs.append((key,attr))
 assert any(key=='security.selinux' for key,_ in attrs)
 payload=work/f'payload-{len(updated)}';payload.write_bytes(data)
 commands += ['rm '+path,f'write {payload} {path}',f'set_inode_field {path} mode 0{mode|0o100000:o}',f'set_inode_field {path} uid {uid}',f'set_inode_field {path} gid {gid}']
 commands += [f'ea_set -f {attr} {path} {key}' for key,attr in attrs]
 updated[name]=entry['sha256'];metadata[name]=(mode,uid,gid,attrs)
assert 'system/vendor/etc/selinux/precompiled_sepolicy' in updated
batch=work/'update.debugfs';batch.write_text('\n'.join(commands)+'\n');r=subprocess.run(['debugfs','-w','-f',str(batch),str(raw)],capture_output=True,check=True)
(e/'v42-policy-debugfs.log').write_bytes(r.stdout+r.stderr)
for name,digest in updated.items():
 assert sha(dbg('cat /'+name,True))==digest
 mode,uid,gid,attrs=metadata[name];stat=dbg('stat /'+name)
 assert int(re.search(r'Mode:\s+([0-7]+)',stat)[1],8)==mode and int(re.search(r'User:\s+(\d+)',stat)[1])==uid and int(re.search(r'Group:\s+(\d+)',stat)[1])==gid
 for key,attr in attrs:
  check=work/'check-attr';dbg(f'ea_get -f {check} /{name} {key}');assert check.read_bytes()==attr.read_bytes()
assert sha(dbg('cat /system/vendor/etc/selinux/precompiled_sepolicy',True))==meta['bootstrap_policy_sha256']
ns={};exec((p/'scripts/verify_system_image_fit.py').read_text().split('if __name__',1)[0],ns);fs=ns['inspect_ext4'](raw);assert fs['fsck_exit']==0
record=dict(status='PERSISTENT_POLICY_IMAGE_VERIFIED',updated_files=updated,ext4=fs,bootstrap_policy_sha256=meta['bootstrap_policy_sha256'],metadata_and_labels_preserved=True,
 unchanged_scope='Exact verified v41 clone; only listed SELinux regular-file contents replaced. APKs, hardware modules and all other file data retained.')
(e/'v42-image-edit.json').write_text(json.dumps(record,indent=2)+'\n');print(record['status'],len(updated),flush=True)
