"""Add only validated host-built Search OAT/VDEX to an exact v39 image clone."""
from pathlib import Path
import hashlib,json,os,re,struct,subprocess,sys,zipfile
assert os.environ.get('WSL_DISTRO_NAME')=='Ubuntu'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
observed='--runtime-paths' in sys.argv
stage=p/'evidence/ui-system-hang-20261112'/('private-search-runtime-preopt' if observed else 'private-search-preopt');manifest=json.loads((stage/'manifest.json').read_text())
assert manifest['status']=='HOST_SEARCH_PREOPT_COMPILED_NOT_INSTALLED'
assert manifest['runtime_boot_images_match'] and not manifest['uses_library_checks_relaxed'] and not manifest['apk_modified']
package=stage/'Velvet-preopt.zip';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(package)==manifest['zip_sha256']
version=41 if observed else 40
a=p/f'artifacts/lineage20-rom-v{version}-gapps';raw=a/'system.raw.incoming';work=Path(f'/root/t110-build/ui-v{version}-search-preopt')
assert not work.exists(),'Inspect any incomplete image edit before restarting'
work.mkdir()
def dbg(command,binary=False):
    r=subprocess.run(['debugfs','-R',command,str(raw)],capture_output=True,check=True)
    return r.stdout if binary else r.stdout.decode(errors='replace')
apk='/system/product/priv-app/Velvet/Velvet.apk';dump=work/'Velvet.apk'
dbg(f'dump {apk} {dump}');assert sha(dump)==manifest['apk_sha256'];dump.unlink()
label=work/'selinux';dbg(f'ea_get -f {label} {apk} security.selinux');assert label.read_bytes().startswith(b'u:object_r:')
with raw.open('rb') as stream:stream.seek(1024);superblock=stream.read(1024)
free=struct.unpack_from('<I',superblock,12)[0]*(1024<<struct.unpack_from('<I',superblock,24)[0])
commands=[];entries={}
parent=json.loads((p/'artifacts/lineage20-rom-v40-gapps/host-verification.json').read_text()) if observed else None
old_bytes=0
if observed:
    assert manifest['observed_runtime_library_paths']
    for name in manifest['files']:
        data=dbg('cat /'+name,True);assert hashlib.sha256(data).hexdigest()==parent['updated_files'][name];old_bytes+=len(data)
with zipfile.ZipFile(package) as archive:
    assert archive.namelist()==manifest['files']
    assert sum(entry.file_size for entry in archive.infolist())+8*1024*1024<free+old_bytes,('Preopt exceeds image headroom',free,old_bytes)
    for directory in ['/system/product/priv-app/Velvet/oat','/system/product/priv-app/Velvet/oat/arm']:
        if observed:assert 'Type: directory' in dbg('stat '+directory)
        else:
            assert 'Inode:' not in dbg('stat '+directory),'Unexpected existing Search OAT; inspect first'
            commands += ['mkdir '+directory,f'set_inode_field {directory} mode 040755',f'set_inode_field {directory} uid 0',f'set_inode_field {directory} gid 0',f'ea_set -f {label} {directory} security.selinux']
    for index,entry in enumerate(archive.infolist()):
        assert entry.filename.startswith('system/product/priv-app/Velvet/oat/arm/') and entry.filename.endswith(('.odex','.vdex'))
        path='/'+entry.filename;data=archive.read(entry);f=work/f'payload-{index}';f.write_bytes(data)
        if entry.filename.endswith('.odex'):assert data[:6]==b'\x7fELF\1\1' and struct.unpack_from('<H',data,18)[0]==40
        if observed:commands.append('rm '+path)
        commands += [f'write {f} {path}',f'set_inode_field {path} mode 0100644',f'set_inode_field {path} uid 0',f'set_inode_field {path} gid 0',f'ea_set -f {label} {path} security.selinux']
        entries[entry.filename]=dict(file=f,sha256=sha(f),bytes=len(data))
batch=work/'update.debugfs';batch.write_text('\n'.join(commands)+'\n')
r=subprocess.run(['debugfs','-w','-f',str(batch),str(raw)],capture_output=True,check=True)
(stage/'image-debugfs.txt').write_bytes(r.stdout+r.stderr)
for name,entry in entries.items():
    assert hashlib.sha256(dbg('cat /'+name,True)).hexdigest()==entry['sha256']
    stat=dbg('stat /'+name);assert re.search(r'Mode:\s+0644',stat) and re.search(r'User:\s+0\s+Group:\s+0',stat)
    check=work/'check-label';dbg(f'ea_get -f {check} /{name} security.selinux');assert check.read_bytes()==label.read_bytes()
namespace={};exec((p/'scripts/verify_system_image_fit.py').read_text().split('if __name__',1)[0],namespace)
fs=namespace['inspect_ext4'](raw);assert fs['fsck_exit']==0
record=dict(status='SEARCH_OAT_IMAGE_FILESYSTEM_VERIFIED',ext4=fs,updated_files={name:entry['sha256'] for name,entry in entries.items()},
            unchanged_apk_sha256=manifest['apk_sha256'],source=manifest,new_files_root_owned_0644=True,selinux_label_preserved=True,
            image_headroom_before=free,features_removed=False,ui_fixed=False)
(stage/'image-edit.json').write_text(json.dumps(record,indent=2)+'\n');print(record['status'],flush=True)
