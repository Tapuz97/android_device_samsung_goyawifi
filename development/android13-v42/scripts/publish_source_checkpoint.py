"""Public source-only checkpoint. Exact private originals remain in draft archives."""
from pathlib import Path
import os,subprocess,shutil,re,json,hashlib
r=Path(__file__).resolve().parents[1];repo=r/'community/device-checkpoint'
assert json.loads(subprocess.check_output(['gh','api','user'],text=True))['login']=='Tapuz97'
branch='t110/android13-v42-checkpoint'
def git(*a):return subprocess.check_output(['git','-C',str(repo),*a],text=True,stderr=subprocess.PIPE).strip()
if git('branch','--show-current')!=branch:git('switch','-c',branch)
dest=repo/'development/android13-v42';dest.mkdir(parents=True,exist_ok=True)
ext={'.c','.cpp','.h','.mk','.bp','.xml','.rc','.te','.kl','.sh','.py','.config','.json','.md','.txt','.kcm','.idc','.prop','.map','.aidl','.java','.gradle','.s','.patch','.gitignore','.bat','.ps1'}
copies=[]
def add(p,relative):
    if p.suffix.lower() not in ext and p.name not in {'Android.mk','Android.bp','Makefile'}:return
    if p.stat().st_size>5*1024*1024:return
    raw=p.read_bytes()
    if b'\0' in raw:return
    try:text=raw.decode('utf-8',errors='strict')
    except UnicodeDecodeError:text=raw.decode('cp1252',errors='strict')
    text=text.replace('T110_ADB_SERIAL','T110_ADB_SERIAL').replace('1101003030384745T110_ADB_SERIAL','T110_EMMC_CID')
    text=re.sub(r'(?i)(?<![0-9a-f])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![0-9a-f])','00:00:00:00:00:00',text)
    target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf-8',newline='\n')
    copies.append({'path':relative.as_posix(),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
for directory in ['work','patches','scripts']:
 for base,dirs,files in os.walk(r/directory,followlinks=False):
    dirs[:]=[x for x in dirs if x not in {'private-preopt','__pycache__','venv','.git'} and not os.path.isjunction(Path(base)/x)]
    for name in files:
        p=Path(base)/name
        if not p.is_symlink():add(p,p.relative_to(r))
for p in r.glob('*.md'):add(p,p.relative_to(r))
for name in ['sources.lock.json','BUILD-WORKSPACE.json']:
    add(r/name,Path(name))
delta=r/'backups/android13-before-lineage14-20261112/lineage20-source-delta'
for p in delta.rglob('*.patch'):add(p,Path('source-delta')/p.relative_to(delta))
add(delta/'pinned-manifest.xml',Path('pinned-manifest.xml'))
for name in ['primary-provenance.json','additional-primary-provenance.json','ALL-PRIMARY-SOURCES.json','blob-textrel.json','source-checks.json']:
    add(r/'evidence/lineage14-audit'/name,Path('audit-evidence')/name)
(dest/'README.md').write_text('''# SM-T110 Android13 preservation and Nougat source audit

Development checkpoint, not a stable ROM or flashable release. Installed Android13
v42/BOOT48 has unresolved graphics, responsiveness and physical wake failures.
See LINEAGE14-GPU-AND-SLEEP-AUDIT.md for the source audit and hardware gates before
building a complete Android7.1 product. No Nougat boot/runtime PASS is claimed.

This branch retains canonical bring-up source, operator scripts, numbered patches,
the pinned Android13 manifest and exact repo-managed source diffs. Device serial,
eMMC CID and MAC addresses were replaced in the PUBLIC copy. Adapt the device
identity checks before using operator scripts; do not flash another device.

Private original source, logs, stock firmware, Google binaries and current/rollback
images belong in the owner's unpublished draft backup, not this public tree.
The root inherited device product is not silently replaced by this WIP checkpoint.
Do not use the old Android13 build steps as completed Nougat build instructions.

Upstream review: https://review.lineageos.org/c/LineageOS/android_build_soong/+/513083
''')
(dest/'source-checkpoint-manifest.json').write_text(json.dumps(copies,indent=2)+'\n')
git('config','user.name','Gal Mitrani');git('config','user.email','103029727+Tapuz97@users.noreply.github.com')
git('add','development/android13-v42')
whitespace=subprocess.run(['git','-C',str(repo),'diff','--cached','--check'],text=True,stdout=subprocess.PIPE)
(r/'community/source-checkpoint-whitespace.txt').write_text(whitespace.stdout)
git('commit','-m','t110: preserve Android13 source and audit Nougat graphics and sleep')
git('push','-u','origin',branch)
head=git('rev-parse','HEAD');remote=git('ls-remote','origin','refs/heads/'+branch).split()[0]
assert head==remote
result={'repository':'Tapuz97/android_device_samsung_goyawifi','branch':branch,'commit':head,'files':len(copies),'remote_verified':True,
 'url':'https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/'+branch,'private_binaries_published':False}
(r/'community/source-checkpoint-publication.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
