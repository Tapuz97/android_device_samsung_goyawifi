"""Back up checked images to a draft release and verify online download hashes."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
WORK=Path(r'\\wsl.localhost\Ubuntu\root\t110-lineage14-ui');ART=WORK/'artifacts-settings-lock-20261115'
REPO='Tapuz97/android_device_samsung_goyawifi'
TAG='t110-lineage14-ui-settings-lock-20261115'
def run(*args,**kwargs):return subprocess.check_output(list(map(str,args)),text=True,**kwargs).strip()
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as source:
        while data:=source.read(1024*1024):h.update(data)
    return h.hexdigest()
report=json.loads((ART/'ui-image-verification.json').read_text(encoding='utf-8'))
assert report['status']=='OFFLINE_COMPLETE_IMAGE_CHECKS_PASSED_NOT_HARDWARE_QUALIFIED'
files={entry['name']:entry for entry in report['files']}
icons=json.loads((ART/'native-icon-verification.json').read_text(encoding='utf-8'))
assert icons['status']=='PASS_ACTUAL_IMAGE_ICON_PIXELS_AND_LAUNCHER_MANIFESTS'
assert icons['system_image_sha256']==files['system.raw.img']['sha256']
for name,entry in files.items():assert digest(ART/name)==entry['sha256'],name
commit=run('wsl','-d','Ubuntu','--','git','-C','/root/t110-lineage14-ui/device','rev-parse','HEAD')
remote=run('wsl','-d','Ubuntu','--','git','-C','/root/t110-lineage14-ui/device','ls-remote','origin',
           'refs/heads/t110/lineage14-modern-ui-20261114').split()[0]
assert remote==commit,'Current UI source must be pushed before backing up the image.'
checksums=''.join(entry['sha256']+'  '+name+'\n' for name,entry in sorted(files.items()))
(ART/'SHA256SUMS.txt').write_text(checksums,encoding='utf-8',newline='\n')
notes=ART/'DRAFT-UI-CANDIDATE.md'
notes.write_text('''Internal development candidate, not a public release.

Native modern UI plus unified navigation settings, native Back/search and screenshot-free lock fading on the working Android7.1.2 / LineageOS14.1 backend.
No Google apps are included. Physical-screen/touch/hardware checks remain pending.
Source commit: '''+commit+'''

The boot image is unchanged from the preserved working14.1 release.
This particular tablet has a faulty physical SYSTEM partition and uses a
loop-mounted userdata system container. Do not flash system.raw.img to SYSTEM.
The device-specific development installer verifies the exact tablet identity,
preserves its old boot/recovery/data and retains the old system container.
''',encoding='utf-8',newline='\n')
view=subprocess.run(['gh','release','view',TAG,'--repo',REPO,'--json','id,isDraft,assets,url'],capture_output=True,text=True)
if view.returncode:
    print('Creating draft UI candidate backup.',flush=True)
    run('gh','release','create',TAG,'--repo',REPO,'--target',commit,'--draft',
        '--title','SM-T110 native modern UI development candidate (Android 7.1.2)',
        '--notes-file',notes)
    release=json.loads(run('gh','release','view',TAG,'--repo',REPO,'--json','id,isDraft,assets,url'))
else:release=json.loads(view.stdout)
assert release['isDraft']
names=('system.raw.img.gz','boot.img','ui-image-verification.json','native-icon-verification.json','settings-lock-verification.json','SHA256SUMS.txt')
existing={asset['name'] for asset in release['assets']}
for name in names:
    if name not in existing:
        print('Uploading '+name,flush=True)
        run('gh','release','upload',TAG,ART/name,'--repo',REPO,timeout=1800)
download_root=WORK/'online-download-check';download_root.mkdir(exist_ok=True)
verified=[]
with tempfile.TemporaryDirectory(prefix='candidate-',dir=download_root) as tmp:
    assert Path(tmp).resolve().is_relative_to(download_root.resolve())
    for name in names:
        print('Verifying online readback: '+name,flush=True)
        run('gh','release','download',TAG,'--repo',REPO,'--pattern',name,'--dir',tmp,timeout=1800)
        actual=digest(Path(tmp)/name);assert actual==digest(ART/name),name
        verified.append({'name':name,'sha256':actual})
receipt={'status':'PASS_ONLINE_DOWNLOAD_HASH_READBACK','release_id':release['id'],
         'tag':TAG,'source_commit':commit,'draft':True,
         'system_gzip_sha256':files['system.raw.img.gz']['sha256'],'verified_assets':verified}
(ART/'online-backup-verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Online UI source and candidate-image backup verified; working14.1 backup remains intact.',flush=True)
