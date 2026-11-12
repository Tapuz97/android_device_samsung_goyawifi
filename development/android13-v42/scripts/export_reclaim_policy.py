"""Export only checked policy outputs before the external build distro exits."""
from pathlib import Path
import hashlib,json,os,re,shutil,struct,subprocess
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/ui-system-hang-20261112'
root=Path('/root/t110-build/lineage20');product=Path('/root/t110-build/out-system/target/product/t110_bringup');dest=e/'reclaim-policy-components';dest.mkdir(exist_ok=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
for name,change in json.loads((e/'reclaim-policy-source.json').read_text()).items():
 assert sha(root/'device/samsung/t110_bringup/sepolicy'/name)==change['after']
log=(e/'reclaim-policy-build.log').read_bytes();assert b'build completed successfully' in log and b'\0' not in log
binary=product/'root/sepolicy';data=binary.read_bytes();size=struct.unpack_from('<I',data,4)[0]
assert data[8:8+size]==b'SE Linux' and struct.unpack_from('<I',data,8+size)[0]==30
assert data==(product/'system/vendor/etc/selinux/precompiled_sepolicy').read_bytes() and b'proc_t110_swappiness' in data
analyzer=Path('/root/t110-build/out-system/host/linux-x86/bin/checkpolicy')
baseline=p/'evidence/hardware-bt-sd/sepolicy'
old_cil=subprocess.check_output([str(analyzer),'-b','-M','-C','-o','-',str(baseline)])
new_cil=subprocess.check_output([str(analyzer),'-b','-M','-C','-o','-',str(binary)])
old_permissive=sorted(re.findall(rb'\(typepermissive\s+([^\s)]+)\)',old_cil))
new_permissive=sorted(re.findall(rb'\(typepermissive\s+([^\s)]+)\)',new_cil))
assert old_permissive==new_permissive,'Unexpected permissive-domain change'
node=[line.decode() for line in new_cil.splitlines() if b'genfscon' in line and b'/sys/vm/swappiness' in line]
assert len(node)==1 and 'proc_t110_swappiness' in node[0],node
files={}
for directory in ['system/etc/selinux','system/vendor/etc/selinux','system/system_ext/etc/selinux','system/product/etc/selinux']:
 for source in sorted((product/directory).rglob('*')):
  if not source.is_file() or source.is_symlink():continue
  name=str(source.relative_to(product));local=dest/name;local.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,local)
  assert sha(local)==sha(source);files[name]=dict(file=name,sha256=sha(local),bytes=local.stat().st_size)
shutil.copyfile(binary,dest/'sepolicy')
record=dict(status='STANDARD_POLICY_COMPILED_EXPORTED',policy_version=30,bootstrap_policy_sha256=sha(binary),files=files,
            exact_new_proc_node='/sys/vm/swappiness',only_new_init_permission_type='proc_t110_swappiness',enforcing_retained=True,
            permissive_domains_unchanged=[name.decode() for name in new_permissive],compiled_exact_node=node[0],freeze_and_neverallow_checks_disabled=False)
(dest/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print('RECLAIM_POLICY_EXPORTED',record['bootstrap_policy_sha256'],flush=True)
