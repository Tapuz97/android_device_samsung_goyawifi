"""Run the candidate's real ARM linkerconfig/linker inside a private filesystem.

No tablet access, LD search overrides, SDK lowering, HAL-device opens or image
writes. The host kernel/QEMU cannot validate PXA988 hardware or Linux3.4 behavior.
"""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys

AUDIT = Path('/root/t110-android13-audit')
TOOLS = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/android13-audit')
IMAGE = AUDIT / 'complete-image/system.raw.img'

def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def manifest_name(directory):
    j=directory/'apex_manifest.json'
    if j.is_file():return json.loads(j.read_text())['name']
    data=(directory/'apex_manifest.pb').read_bytes();pos=0
    def varint():
        nonlocal pos
        value=0
        for shift in range(0,70,7):
            byte=data[pos];pos+=1;value|=(byte&127)<<shift
            if not byte&128:return value
        raise ValueError('Invalid manifest varint')
    while pos<len(data):
        key=varint();wire=key&7;field=key>>3
        if wire==2:
            n=varint();value=data[pos:pos+n];pos+=n
            if field==1:return value.decode()
        elif wire==0:varint()
        elif wire in (1,5):pos+=8 if wire==1 else 4
        else:raise ValueError('Unexpected manifest wire type')
    raise ValueError('Missing APEX manifest name')

def is_dynamic_arm(path):
    # Inspect real files only; never follow guest absolute symlinks on the host.
    if path.is_symlink() or not path.is_file():return False
    with path.open('rb') as f:
        header=f.read(52)
        if header[:4]!=b'\x7fELF':return False
        assert header[4:6]==b'\x01\x01' and struct.unpack_from('<H',header,18)[0]==40,path
        offset=struct.unpack_from('<I',header,28)[0]
        size,count=struct.unpack_from('<HH',header,42)
        dynamic=False;interp=False
        for i in range(count):
            f.seek(offset+size*i);ph=f.read(size)
            kind=struct.unpack_from('<I',ph)[0]
            if kind==3:interp=True
            if kind==2:
                start,bytes_=struct.unpack_from('<I',ph,4)[0],struct.unpack_from('<I',ph,16)[0]
                after=f.tell();f.seek(start);table=f.read(bytes_);f.seek(after)
                dynamic=any(struct.unpack_from('<I',table,n)[0]==1 for n in range(0,len(table)-7,8))
        return dynamic or interp

def install_qemu_runtime(root):
    dest=root/'.qemu';libs=dest/'lib';libs.mkdir(parents=True)
    binary=Path('/usr/bin/qemu-arm')
    shutil.copy2(binary,dest/'qemu-arm')
    dependencies=subprocess.check_output(['ldd',str(binary)],text=True)
    paths=re.findall(r'=> (/\S+)',dependencies)
    loader=Path('/lib64/ld-linux-x86-64.so.2')
    shutil.copy2(loader,dest/'ld-linux-x86-64.so.2')
    for item in paths:shutil.copy2(item,libs/Path(item).name)
    return dict(binary_sha256=digest(binary),host_dependencies=paths)

def child(work):
    # Everything mounted below lives in this process's private mount namespace.
    run(['mount','--make-rprivate','/'])
    lower=work/'lower';root=work/'root'
    run(['mount','-o','loop,ro,noload',IMAGE,lower])
    run(['mount','-t','overlay','overlay','-o',
         f'lowerdir={lower},upperdir={work}/upper,workdir={work}/overlay-work',root])
    # Match the preserved boot stage's real canonical partition-root mounts.
    for name in ('product','system_ext'):
        target=root/name
        if target.is_symlink():target.unlink()
        target.mkdir(exist_ok=True)
        source=root/'system'/name
        assert source.is_dir(),source
        run(['mount','--bind',source,target])
        run(['mount','-o','remount,bind,ro',target])
    apexes={}
    for partition in ('system','system/system_ext','system/product','system/vendor'):
        apexdir=root/partition/'apex'
        if not apexdir.is_dir():continue
        for source in sorted(apexdir.iterdir()):
            if source.is_symlink() or not source.is_dir():continue
            if not (source/'apex_manifest.pb').is_file():continue
            name=manifest_name(source)
            assert name not in apexes,('Multiple active flattened APEX candidates',name)
            target=root/'apex'/name;target.mkdir(parents=True,exist_ok=True)
            run(['mount','--bind',source,target])
            run(['mount','-o','remount,bind,ro',target])
            apexes[name]=str(source.relative_to(root))
    assert {'com.android.runtime','com.android.art','com.android.i18n'}<=set(apexes),apexes
    (root/'proc').mkdir(exist_ok=True);run(['mount','--bind','/proc',root/'proc'])
    for name,minor in (('null',3),('zero',5),('random',8),('urandom',9)):
        p=root/'dev'/name
        if not p.exists():os.mknod(p,stat.S_IFCHR|0o666,os.makedev(1,minor))
    (root/'dev/kmsg').touch()
    host_runtime=install_qemu_runtime(root)
    diag=root/'data/local/tmp';diag.mkdir(parents=True,exist_ok=True)
    shutil.copy2(AUDIT/'namespace-tools/candidate-namespace-probe',diag/'candidate-namespace-probe')
    context_files=[]
    for partition,prefix in (('system','plat'),('system/system_ext','system_ext'),
                             ('system/product','product'),('system/vendor','vendor'),('system/odm','odm')):
        p=root/partition/'etc/selinux'/f'{prefix}_property_contexts'
        if p.is_file():context_files.append(p)
    propdir=root/'dev/__properties__';propdir.mkdir(exist_ok=True)
    run([AUDIT/'namespace-tools/candidate-property-info',propdir/'property_info',*context_files])
    props={}
    prop_inputs=[]
    for partition in ('system','system/system_ext','system/product','system/vendor','system/odm'):
        for relative in ('etc/prop.default','build.prop'):
            path=root/partition/relative
            if not path.is_file():continue
            prop_inputs.append(dict(path=str(path.relative_to(root)),sha256=digest(path)))
            for line in path.read_text().splitlines():
                line=line.strip()
                if not line or line.startswith('#') or '=' not in line:continue
                key,value=line.split('=',1);props[key.strip()]=value.strip()
    assert props.get('ro.build.version.sdk')=='33',props.get('ro.build.version.sdk')
    assert props.get('ro.t110.legacy_audio') in ('true','1')
    assert props.get('ro.t110.legacy_gpu') in ('true','1')
    assert props.get('ro.apex.updatable')=='false',props.get('ro.apex.updatable')
    assert not props.get('ro.vndk.version'),'Fixture currently expects the actual legacy product'
    propfile=diag/'candidate.properties'
    propfile.write_text(''.join(k+'='+v+'\n' for k,v in sorted(props.items())))
    env=os.environ.copy()
    for name in ('LD_LIBRARY_PATH','LD_PRELOAD','T110_PROBE_LEGACY_SDK'):env.pop(name,None)
    # This is the actual ALSA environment entry in the candidate's init override.
    rc=(root/'system/vendor/etc/init/init.t110.audio.rc').read_text()
    match=re.search(r'^\s*setenv ALSA_CONFIG_PATH (\S+)',rc,re.M)
    assert match,rc
    env['ALSA_CONFIG_PATH']=match[1]
    commands=[]
    def guest(binary,args=(),required=True):
        cmd=['chroot',str(root),'/.qemu/ld-linux-x86-64.so.2','--library-path','/.qemu/lib',
             '/.qemu/qemu-arm','-cpu','cortex-a9',binary,*args]
        result=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=60)
        item=dict(binary=binary,args=list(args),exit=result.returncode,stdout=result.stdout,stderr=result.stderr)
        commands.append(item)
        if required and result.returncode:
            (work/'partial-results.json').write_text(json.dumps(commands,indent=2)+'\n')
            raise RuntimeError(item)
        return item
    generator='/system/bin/bootstrap/linkerconfig'
    # Static generator can bootstrap the dynamic writer. Only the regenerated
    # configuration made AFTER actual properties exist counts as production.
    guest(generator,['--target','/linkerconfig','--strict'])
    guest('/data/local/tmp/candidate-namespace-probe',['properties','/data/local/tmp/candidate.properties'])
    guest('/data/local/tmp/candidate-namespace-probe',['get','ro.build.version.sdk','33'])
    guest('/data/local/tmp/candidate-namespace-probe',['get','ro.t110.legacy_audio',props['ro.t110.legacy_audio']])
    guest(generator,['--target','/linkerconfig','--strict'])
    configs=[]
    for p in sorted((root/'linkerconfig').rglob('ld.config.txt')):
        text=p.read_text()
        assert '/.qemu' not in text and '/root/t110' not in text,p
        configs.append(dict(path=str(p.relative_to(root)),sha256=digest(p)))
    config=(root/'linkerconfig/ld.config.txt').read_text()
    assert '[legacy]' in config and 'namespace.default.isolated = false' in config,config[:3000]
    assert len(configs)>1,'No isolated APEX executable configurations generated'
    # Constructor-free loading of all dynamic native programs and all vendor
    # libraries also covers graphics blobs whose old build skipped ELF checks.
    targets=set()
    trees=[(root/'system/bin','/system/bin'),(root/'system/vendor/bin','/vendor/bin'),
           (root/'system/vendor/lib','/vendor/lib')]
    trees += [(root/'apex'/name/'bin','/apex/'+name+'/bin') for name in apexes]
    for tree,prefix in trees:
        if not tree.is_dir():continue
        for parent,_,files in os.walk(tree,followlinks=False):
            for filename in files:
                p=Path(parent)/filename
                if is_dynamic_arm(p):targets.add(prefix+'/'+str(p.relative_to(tree)))
    linker='/apex/com.android.runtime/bin/linker'
    failures=[]
    for target in sorted(targets):
        item=guest(linker,['--list',target],required=False)
        if item['exit']:failures.append(item)
    # Actual dlopen in the same generated legacy service namespace, with normal
    # SDK behavior. No HMI open/read/write or GPU initialization is called.
    audio=['/vendor/lib/hw/audio.primary.t110.so','/vendor/lib/hw/audio.primary.mrvl.so',
           '/vendor/lib/alsa-lib/libasound_module_ctl_codec.so',
           '/vendor/lib/alsa-lib/libasound_module_ctl_phone.so',
           '/vendor/lib/alsa-lib/libasound_module_pcm_phone.so',
           '/vendor/lib/hw/android.hardware.audio@7.1-impl.so',
           '/vendor/lib/hw/android.hardware.audio.effect@7.0-impl.so']
    loaded=guest('/data/local/tmp/candidate-namespace-probe',['load',*audio],required=False)
    if loaded['exit']:failures.append(loaded)
    # Exact-path textrel restriction: an identical DSP at an unrelated path must
    # remain rejected, even with the device's real opt-in property enabled.
    shutil.copy2(root/'system/vendor/lib/libippsp.so',diag/'libippsp-unrelated.so')
    rejected=guest(linker,['--list','/data/local/tmp/libippsp-unrelated.so'],required=False)
    assert rejected['exit'] and 'text relocations' in rejected['stderr'],rejected
    result=dict(status='FAIL' if failures else 'PASS',image_sha256=digest(IMAGE),
        fixture=str(work),apexes=apexes,configs=configs,property_inputs=prop_inputs,
        property_count=len(props),native_load_targets=len(targets),failures=failures,commands=commands,
        sdk_lowered=False,ld_overrides=False,constructor_free_checks=True,
        host_runtime=host_runtime,hardware_opened=False,selinux_runtime_enforced=False,
        kernel_emulated=False,flashed=False)
    (AUDIT/'production-namespace-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    # Preserve the actual generated configuration text, not only its hashes.
    shutil.copytree(root/'linkerconfig',work/'generated-linkerconfig',symlinks=True)
    print(f"{result['status']}: {len(targets)} native load targets, {len(configs)} real namespace configs; {len(failures)} failures.")
    if failures:sys.exit(1)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--in-namespace':
        child(Path(sys.argv[2]))
    else:
        assert IMAGE.is_file() and IMAGE.stat().st_size==2146435072,IMAGE
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        work=AUDIT/'namespace-fixtures'/stamp
        for name in ('lower','root','upper','overlay-work'):(work/name).mkdir(parents=True,exist_ok=False)
        cmd=['unshare','--mount','--pid','--fork','--mount-proc','python3',__file__,'--in-namespace',str(work)]
        log=work/'namespace-run.log'
        with log.open('w') as output:
            result=subprocess.run(cmd,stdout=output,stderr=subprocess.STDOUT)
        print(log.read_text()[-10000:])
        raise SystemExit(result.returncode)
