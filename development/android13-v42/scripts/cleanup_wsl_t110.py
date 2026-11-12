"""Remove only the dedicated Ubuntu T110 build tree after verified online backup."""
from pathlib import Path
import json,os,subprocess,shutil
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
proof=json.loads((project/'backups/android13-before-lineage14-20261112/FINAL-ONLINE-VERIFIED.json').read_text())
assert proof['all_required_payloads_download_hash_verified'] and proof['full_restoration_archive_member_hash_verified']
assert proof['kernel_commit']=='3eb98fe728aefa780638a1bb2f487e19ba6fadcb'
target=Path('/root/t110-build')
assert target.resolve()==target and not target.is_symlink() and target.parent==Path('/root')
if target.exists():
 mounts=json.loads(subprocess.check_output(['findmnt','--json','--list','--output','TARGET,SOURCE'],text=True))['filesystems']
 descendants=[m for m in mounts if m['target']==str(target) or m['target'].startswith(str(target)+'/')]
 assert not descendants,('Unmount nested filesystems before removing the task tree',descendants)
 config=target/'out-standard-reclaim/.config'
 assert (target/'kernel-display-i2c/Documentation/t110-android13-checkpoint.md').exists()
 assert (target/'kernel-display-i2c/.git').is_dir()
 active=[]
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
  try:
   cwd=(proc/'cwd').resolve()
   args=(proc/'cmdline').read_bytes().replace(b'\0',b' ')
   if cwd==target or target in cwd.parents or b'/root/t110-build' in args:active.append(proc.name)
  except (OSError,RuntimeError):pass
 assert not active,('Processes still using the task tree',active)
 before=shutil.disk_usage('/').free
 shutil.rmtree(target)
 assert not target.exists()
 subprocess.run(['sync'],check=True)
 trim=subprocess.run(['fstrim','-v','/'],text=True,capture_output=True)
 result={'removed':'/root/t110-build','free_before':before,'free_after':shutil.disk_usage('/').free,
         'trim_exit_code':trim.returncode,'trim_output':trim.stdout.strip() or trim.stderr.strip()}
else:result={'removed':'/root/t110-build','already_absent':True}
(project/'CLEANUP-UBUNTU.md').write_text('# Ubuntu T110 cleanup result\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n')
print(json.dumps(result,indent=2))
