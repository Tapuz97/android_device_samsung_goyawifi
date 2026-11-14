from pathlib import Path
import subprocess,os,shutil,json,time
root=Path('/root/t110-android13')
android=root/'android';android.mkdir(parents=True,exist_ok=True)
audit=Path('/root/t110-android13-audit')
logs=root/'logs';logs.mkdir(exist_ok=True)
env=os.environ.copy();env['GIT_TERMINAL_PROMPT']='0';env['GIT_LFS_SKIP_SMUDGE']='1'
env['PATH']='/usr/local/bin:/usr/bin:/bin'
def run(command,name):
 with (logs/name).open('w') as out:
  p=subprocess.run(command,cwd=android,env=env,stdout=out,stderr=subprocess.STDOUT)
 if p.returncode:raise SystemExit('Failed '+name+' exit='+str(p.returncode))
if not (android/'.repo/repo').exists():
 run(['repo','init','-u','https://github.com/LineageOS/android.git','-b','lineage-20.0','--depth=1','--no-clone-bundle'],'repo-init.log')
manifest=audit/'restored/source-delta/pinned-manifest.xml'
dest=android/'.repo/manifests/t110-pinned.xml';shutil.copy2(manifest,dest)
link=android/'.repo/manifest.xml'
if link.is_symlink() or link.exists():link.unlink()
link.symlink_to('manifests/t110-pinned.xml')
print('Syncing exact Android13 checkpoint projects into',android,flush=True)
run(['repo','sync','-c','--no-clone-bundle','--no-tags','--optimized-fetch','-j8'],'repo-sync.log')
(root/'SYNC-COMPLETE.json').write_text(json.dumps(dict(status='PINNED_SOURCE_SYNC_COMPLETE',manifest=str(manifest)))+'\n')
print('Pinned source sync completed.',flush=True)
