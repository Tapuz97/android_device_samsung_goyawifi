"""Use the ROM's normal host ART compiler for the unchanged, private Google APK.

No Google APK is added to the public device tree. Generated install ZIP contains
only OAT/VDEX, never a replaced, resigned or modified APK. Library checking stays
enabled and the actual installed boot images must match the build's images.
"""
from pathlib import Path
import hashlib,json,os,shutil,struct,subprocess,sys,time,zipfile
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
root=Path('/root/t110-build');tree=root/'lineage20';out=root/'out-system';product=out/'target/product/t110_bringup'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
e=p/'evidence/ui-system-hang-20261112';observed='--runtime-paths' in sys.argv
dest=e/('private-search-runtime-preopt' if observed else 'private-search-preopt');dest.mkdir(exist_ok=True)
work=out/('private-search-runtime-preopt' if observed else 'private-search-preopt');work.mkdir(exist_ok=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
original=json.loads((p/'artifacts/lineage20-rom-v39-gapps/host-verification.json').read_text())
expected=original['gapps_files']['system/product/priv-app/Velvet/Velvet.apk']
apk=work/'Velvet.apk'
if not apk.exists():
    cached=out/'private-search-preopt/Velvet.apk'
    if observed and cached.exists():
        assert sha(cached)==expected;os.link(cached,apk)
if not apk.exists():
    archive=p/'artifacts/mindthegapps-arm13/MindTheGapps-13.0.0-arm-20231025_200806.zip'
    assert sha(archive)==original['gapps_zip_sha256']
    with zipfile.ZipFile(archive) as source_zip,source_zip.open('system/product/priv-app/Velvet/Velvet.apk') as source,apk.open('wb') as target:
        shutil.copyfileobj(source,target)
assert sha(apk)==expected
with zipfile.ZipFile(apk) as archive,apk.open('rb') as stream:
    dex_files=[entry for entry in archive.infolist() if entry.filename.endswith('.dex')]
    assert dex_files
    for entry in dex_files:
        assert entry.compress_type==zipfile.ZIP_STORED
        stream.seek(entry.header_offset+26)
        name_length,extra_length=struct.unpack('<HH',stream.read(4))
        assert (entry.header_offset+30+name_length+extra_length)%4==0
for line in (e/'runtime-art-inputs.sha256').read_text().splitlines():
    digest,name=line.split()
    relative=name.lstrip('/')
    if relative.startswith('system_ext/'):relative='system/'+relative
    assert sha(product/relative)==digest,('Host/runtime ART or library mismatch',name)
tools=json.loads((out/'soong/dexpreopt_soong.config').read_text())
libraries=['org.apache.http.legacy','androidx.window.extensions','androidx.window.sidecar']
status=work/'uses-libraries.status'
command=[tools['ManifestCheck'],'--enforce-uses-libraries','--enforce-uses-libraries-status',str(status),'--aapt',tools['Aapt']]
for name in libraries:command+=['--optional-uses-library',name]
subprocess.run(command+[str(apk)],check=True,cwd=tree)
assert status.read_text()==''
config=json.loads((out/'soong/.intermediates/packages/apps/Trebuchet/TrebuchetQuickStep/android_common/dexpreopt/dexpreopt.config').read_text())
config.update(Name='Velvet',DexLocation='/system/product/priv-app/Velvet/Velvet.apk',UncompressedDex=True,PresignedPrebuilt=True,
              HasApkLibraries=False,PreoptExtractedApk=False,NoCreateAppImage=True,ForceCreateAppImage=False,
              BuildPath=str(work/'dexpreopt/Velvet.jar'),DexPath=str(apk),ManifestPath='',ProvidesUsesLibrary='Velvet',
              ProfileClassListing='',ProfileBootListing='',EnforceUsesLibraries=True,EnforceUsesLibrariesStatusFile=str(status))
config['ClassLoaderContexts']={'any':[
    dict(Name=name,Optional=True,Implicit=False,Host=str(product/relative),Device=device,Subcontexts=[])
    for name,relative,device in [
        (libraries[0],'system/framework/org.apache.http.legacy.jar','/system/framework/org.apache.http.legacy.jar'),
        (libraries[1],'system/system_ext/framework/androidx.window.extensions.jar','/system_ext/framework/androidx.window.extensions.jar'),
        (libraries[2],'system/system_ext/framework/androidx.window.sidecar.jar','/system_ext/framework/androidx.window.sidecar.jar')]]}
if observed:
    rejection=(e/'v40-boot46-ui/logcat-after.txt').read_text()
    assert 'expected=/system_ext/framework/androidx.window.extensions.jar, found=/system/system_ext/framework/androidx.window.extensions.jar' in rejection
    for entry in config['ClassLoaderContexts']['any']:
        if entry['Device'].startswith('/system_ext/'):
            entry['Device']='/system'+entry['Device']
global_config=json.loads((out/'soong/dexpreopt.config').read_text())
global_config['SpeedApps']=[name for name in global_config['SpeedApps'] if name!='Velvet']
global_config['DefaultCompilerFilter']='space'
module=work/'module.config';module.write_text(json.dumps(config,indent=2)+'\n')
global_path=work/'global.config';global_path.write_text(json.dumps(global_config,indent=2)+'\n')
script=work/'dexpreopt.sh';package=work/'Velvet-preopt.zip'
subprocess.run([str(out/'host/linux-x86/bin/dexpreopt_gen'),'-global',str(global_path),'-global_soong',str(out/'soong/dexpreopt_soong.config'),'-module',str(module),'-dexpreopt_script',str(script),'-out_dir',str(out)],cwd=tree,check=True)
generated=script.read_text()
assert '--compiler-filter=$(if test -s ' in generated and 'else echo space ; fi)' in generated
assert '--instruction-set-variant=cortex-a9' in generated and status.read_text()==''
assert '${class_loader_context_arg} ${stored_class_loader_context_arg}' in generated
assert '--host-context-for-sdk any PCL[' in generated and 'org.apache.http.legacy.jar' in generated
assert '--force-determinism' in generated
assert '--copy-dex-files=false' in generated
for name in ['module.config','global.config','dexpreopt.sh','uses-libraries.status']:shutil.copyfile(work/name,dest/name)
log=dest/'host-compiler.log';started=time.monotonic();print('HOST_SEARCH_COMPILATION_STARTED',flush=True)
with log.open('wb') as stream:
    r=subprocess.run(['bash',str(script),str(apk),str(package)],cwd=tree,stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
assert r.returncode==0,('Host compilation failed',r.returncode)
assert sha(apk)==expected
with zipfile.ZipFile(package) as archive:
    names=archive.namelist();assert names and all(name.startswith('system/product/priv-app/Velvet/oat/arm/') and name.endswith(('.odex','.vdex')) for name in names),names
    assert any(name.endswith('.odex') for name in names) and any(name.endswith('.vdex') for name in names)
shutil.copyfile(package,dest/package.name)
record=dict(status='HOST_SEARCH_PREOPT_COMPILED_NOT_INSTALLED',seconds=round(time.monotonic()-started,2),apk_sha256=expected,
            compiler_filter='space',cpu='cortex-a9',jit_enabled=False,uses_library_checks_relaxed=False,
            runtime_boot_images_match=True,apk_modified=False,files=names,zip_bytes=package.stat().st_size,zip_sha256=sha(package),
            observed_runtime_library_paths=observed,class_loader_contexts=config['ClassLoaderContexts'],ui_fixed=False)
(dest/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
