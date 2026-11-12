"""Verify the built startup fixes in the exported filesystem, with no device IO."""
from pathlib import Path
import hashlib, json, subprocess, struct, io, zipfile

project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
base=Path('/root/t110-build')
tree=base/'lineage20'
root=base/'export-lineage20-rom-v15'
product=base/'out-system/target/product/t110_bringup'
evidence=project/'evidence/offline-v24'
evidence.mkdir(exist_ok=True)

def content(name):
    return subprocess.check_output(['debugfs','-R','cat '+name,str(root/'system.raw.img')],
                                   stderr=subprocess.DEVNULL)
def sha(data): return hashlib.sha256(data).hexdigest()
def same(path):
    data=content('/'+path)
    assert data == (product/path).read_bytes(),path
    return data

def oat_header(data):
    # This source's OatHeader has magic/version followed by fifteen uint32 fields.
    # Read the actual ELF sections rather than accepting a string anywhere in it.
    assert data[:6]==b'\x7fELF\x01\x01' and struct.unpack_from('<H',data,18)[0]==40
    shoff=struct.unpack_from('<I',data,32)[0]
    shentsize,shnum,shstrndx=struct.unpack_from('<3H',data,46)
    assert shentsize==40 and shstrndx<shnum
    sections=[struct.unpack_from('<10I',data,shoff+i*shentsize) for i in range(shnum)]
    strings=sections[shstrndx]; names=data[strings[4]:strings[4]+strings[5]]
    named={names[s[0]:].split(b'\0',1)[0].decode():s for s in sections}
    text=named['.text']; assert text[5]>0 and text[2]&4 # SHF_EXECINSTR
    ro=named['.rodata']; base=ro[4]
    assert data[base:base+4]==b'oat\n'
    version=data[base+4:base+8].rstrip(b'\0').decode()
    assert version=='225',version # pinned Android 13 ART source
    fields=struct.unpack_from('<15I',data,base+8)
    assert fields[3]>0 and fields[6]>0
    pairs=data[base+68:base+68+fields[14]].split(b'\0')
    assert pairs[-1]==b'' and (len(pairs)-1)%2==0
    metadata={pairs[i].decode():pairs[i+1].decode() for i in range(0,len(pairs)-1,2)}
    assert metadata['compiler-filter']=='speed',metadata
    cursor=base+fields[4]
    location_size=struct.unpack_from('<I',data,cursor)[0]
    location=data[cursor+4:cursor+4+location_size].decode()
    checksum=struct.unpack_from('<I',data,cursor+4+location_size)[0]
    return dict(oat_version=version,dex_files=fields[3],compiled_code_bytes=text[5],metadata=metadata,
                first_dex_location=location,first_dex_checksum=checksum)

prop=content('/system/build.prop')
for value in [b'dalvik.vm.usejit=false',b'dalvik.vm.usejitprofiles=false',
              b'ro.t110.legacy_gpu=true',b'debug.renderengine.backend=gles',
              b'ro.zygote.disable_gl_preload=true',b'ro.t110.optional_hal_probe=true']:
    assert value in prop,value
assert b'ro.t110.optional_hal_probe u:object_r:exported_default_prop:s0 exact bool' in \
    content('/system/vendor/etc/selinux/vendor_property_contexts')

gnss=same('system/lib/libservices.core-gnss.so')
assert b'T110 GNSS probing declared services without waiting' in gnss
lmkd=same('system/bin/lmkd')
assert b'lmkd accepted socket SO_PASSCRED failed' in lmkd
assert b'Failed to retrieve sender credentials' in lmkd # enforcement retained
art=same('system/apex/com.android.art/lib/libart.so')
assert art[:4]==b'\x7fELF'
assert not content('/system/apex/com.android.art/lib/libartd.so')
assert not content('/system/apex/com.android.art.debug/lib/libartd.so')
assert not content('/system/apex/com.android.art.debug/apex_manifest.pb')
# The standard runtime retains the previously built first-fork fix.
old=project/'evidence/v13-combined-fixes-contents.json'
old_art=json.loads(old.read_text())['art']
assert sha(art) in [v['sha256'] for v in old_art if v['path'].endswith('/libart.so')]

render=same('system/bin/surfaceflinger')
assert b'T110 EGL window swap published the exact client target' in render
assert b'T110 resolved GLES frame before handoff' not in render
composer=same('system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service')
assert b'PXA ION read synchronization enabled' in composer
assert b'T110 direct framebuffer presenter ready' in composer
assert b'T110 legacy gralloc: retaining allocation owners in process' in same('system/lib/libui.so')

config=json.loads((base/'out-system/soong/dexpreopt.config').read_text())
assert not config['DisablePreopt']
assert not config['OnlyPreoptBootImageAndSystemServer']
for name in ['PermissionController','SystemUI','TrebuchetQuickStep']:
    assert name in config['SpeedApps']
(evidence/'dexpreopt.config.json').write_text(json.dumps(config,indent=2)+'\n')

oats=[]
for name in ['PermissionController','SystemUI','TrebuchetQuickStep']:
    # Installed application directory can differ from its Soong module name.
    filename='Trebuchet' if name=='TrebuchetQuickStep' else name
    paths=list((product/'system').rglob(filename+'.odex'))
    if name=='PermissionController':
        paths=list((product/'system/framework/oat/arm').glob('apex@com.android.permission@priv-app@PermissionController@*@PermissionController.apk@classes.odex'))
    if not paths and name=='TrebuchetQuickStep':
        paths=list((product/'system').rglob('TrebuchetQuickStep.odex'))
    assert len(paths)==1,(name,paths)
    path=paths[0]; relative=str(path.relative_to(product))
    data=same(relative); assert data[:4]==b'\x7fELF'
    header=oat_header(data)
    location=header['first_dex_location']
    if location.startswith(('/apex/','/system_ext/','/product/')):
        location='/system'+location
    apk=content(location)
    with zipfile.ZipFile(io.BytesIO(apk)) as archive:
        assert archive.getinfo('classes.dex').CRC==header['first_dex_checksum'],name
    assert same(relative.removesuffix('.odex')+'.vdex').startswith(b'vdex')
    if name=='PermissionController':
        assert header['first_dex_location'].startswith('/apex/com.android.permission/priv-app/PermissionController@')
    (evidence/(name+'-oat-header.json')).write_text(json.dumps(header,indent=2)+'\n')
    oats.append(dict(module=name,path=relative,sha256=sha(data),bytes=len(data),
                     compiler_filter='speed',compiled_code_bytes=header['compiled_code_bytes']))

assert json.loads((evidence/'regressions.json').read_text())['status']=='PASS'
sources=[]
for repo,patch in [('frameworks/base','0040-gnss-t110-declared-service-probe.patch'),
                   ('system/memory/lmkd','0041-lmkd-accepted-socket-credentials.patch'),
                   ('art','0039-art-zygote-visibility-checkpoint-lock.patch'),
                   ('build/soong','0042-soong-t110-flattened-apex-app-preopt.patch'),
                   ('build/make','0043-build-t110-standard-art-selection.patch'),
                   ('frameworks/native','0038-renderengine-t110-egl-window-bridge.patch')]:
    subprocess.run(['git','-C',str(tree/repo),'apply','--reverse','--check',
                    str(project/'patches'/patch)],check=True)
    sources.append(dict(repo=repo,base_commit=subprocess.check_output(
        ['git','-C',str(tree/repo),'rev-parse','HEAD'],text=True).strip(),
        patch=patch,sha256=sha((project/'patches'/patch).read_bytes())))
for name in ['t110_system.mk','BoardConfig.mk','sepolicy/property_contexts']:
    local=project/'work/device/samsung/t110_bringup'/name
    assert local.read_bytes()==(tree/'device/samsung/t110_bringup'/name).read_bytes()
    sources.append(dict(device_file=name,sha256=sha(local.read_bytes())))

result=dict(status='PASS',standard_art_apex=True,debug_art_absent=True,
    gnss_declared_service_probe=True,lmkd_credentials_required=True,apps_precompiled=oats,
    retained_graphics=True,retained_art_fork_fix=True,source_provenance=sources,
    gnss_library_sha256=sha(gnss),lmkd_sha256=sha(lmkd),libart_sha256=sha(art),
    tablet_access=False,android_boots=0,hardware_validated=False)
(project/'evidence/v15-startup-fixes-contents.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
