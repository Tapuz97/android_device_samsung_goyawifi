"""Package the complete Nougat system with the proven loop-image boot mechanism."""
from pathlib import Path
import gzip
import hashlib
import json
import shutil
import stat
import struct
import subprocess
import argparse

args_parser=argparse.ArgumentParser()
args_parser.add_argument('--reuse-system',type=Path)
args_parser.add_argument('--reuse-system-sha256')
args=args_parser.parse_args()
BASE=Path('/root/t110-lineage14')
OUT=BASE/'android/out/target/product/goyawifi'
DEST=BASE/'artifacts/lineage14-first-build'
DEVICE=BASE/'android/device/samsung/goyawifi'
BOOT48=BASE/'reference/current-private/artifacts/android13-boot-v48/KERNEL.img'
SYSTEM_SIZE=1594884096
BOOT_SIZE=16777216

def records(raw):
    offset=0
    while True:
        h=raw[offset:offset+110]
        if h[:6]!=b'070701':raise RuntimeError('Invalid cpio header')
        fields=[int(h[i:i+8],16) for i in range(6,110,8)]
        size,namesize=fields[6],fields[11]
        name=raw[offset+110:offset+110+namesize-1].decode()
        offset=(offset+110+namesize+3)&~3
        body=raw[offset:offset+size];offset=(offset+size+3)&~3
        yield name,fields,body
        if name=='TRAILER!!!':return

def entry(name,fields,body):
    values=list(fields);values[6]=len(body);values[11]=len(name.encode())+1
    header=b'070701'+b''.join(('%08x'%x).encode() for x in values)
    blob=header+name.encode()+b'\0';blob+=bytes(-len(blob)%4)
    blob+=body;blob+=bytes(-len(blob)%4)
    return blob

# Fail closed if the full Android7 product or any selected vendor dependency is missing.
properties=dict(line.split('=',1) for line in (OUT/'system/build.prop').read_text().splitlines()
                if line and not line.startswith('#') and '=' in line)
assert properties['ro.build.version.release']=='7.1.2'
assert properties['ro.build.version.sdk']=='25'
assert properties['ro.product.device']=='goyawifi'
assert properties['ro.cm.version'].startswith('14.1-')
subprocess.run(['python3',str(Path(__file__).with_name('verify_lineage14_inputs.py'))],check=True)
subprocess.run(['python3',str(Path(__file__).with_name('verify_window_contract_build.py'))],check=True)
subprocess.run(['python3',str(Path(__file__).with_name('verify_vendor_elf.py'))],check=True)
elf_report=json.loads((BASE/'records/vendor-elf-verification.json').read_text())
assert elf_report['status']=='PASS' and not elf_report['uses_staged_files']
assert len(elf_report['files'])==len(json.loads((DEVICE/'vendor-inputs.json').read_text())['dependencies'])
DEST.mkdir(parents=True,exist_ok=True)
ramdisk=OUT/'ramdisk.img'
stage=(OUT/'system/bin/t110_stage').read_bytes()
assert stage[:6]==b'\x7fELF\1\1' and struct.unpack_from('<H',stage,18)[0]==40
assert not subprocess.check_output(['readelf','-l',str(OUT/'system/bin/t110_stage')],text=True).find('INTERP')>=0
items={n:(f,b) for n,f,b in records(gzip.decompress(ramdisk.read_bytes())) if n!='TRAILER!!!'}
assert 'init' in items and 'sepolicy' in items and 'init.mrvl.rc' in items
init_fields,android_init=items['init'];assert android_init[:4]==b'\x7fELF'
items['init.android']=(init_fields,android_init)
items['init']=(init_fields,stage)
for name,(fields,body) in list(items.items()):
    if stat.S_ISLNK(fields[1]) and Path(name).name in ('ueventd','watchdogd'):
        if body in (b'../init',b'/init'):items[name]=(fields,body.replace(b'init',b'init.android'))
def new_fields(mode):return [0,mode,0,0,1,0,0,0,0,0,0,0,0]
# The loader bind-mounts a private cache; the standard cache symlink would
# fail its directory check (and bind onto its own target). Use real mountpoints.
for name in ('lib','lib/modules','stage-data','cache'):
    if name not in items or not stat.S_ISDIR(items[name][0][1]):items[name]=(new_fields(stat.S_IFDIR|0o755),b'')
items.pop('lib/modules/galcore.ko',None)
assert (OUT/'system/vendor/lib/modules/galcore.ko').read_bytes()==(DEVICE/'prebuilt/galcore.ko').read_bytes()
raw=b''.join(entry(n,f,b) for n,(f,b) in sorted(items.items()))
raw+=entry('TRAILER!!!',new_fields(0),b'');raw+=bytes(-len(raw)%512)
# Reparse the actual generated archive; packaging must preserve Android init and daemon dispatch.
parsed={n:(f,b) for n,f,b in records(raw) if n!='TRAILER!!!'}
assert parsed['init'][1]==stage and parsed['init.android'][1]==android_init
for target in ('dev','proc','sys','system','data','cache','stage-data'):
    assert stat.S_ISDIR(parsed[target][0][1]), 'Bootstrap target must be a real directory: '+target
for daemon in ('sbin/ueventd','sbin/watchdogd'):
    assert stat.S_ISLNK(parsed[daemon][0][1])
    assert parsed[daemon][1] in (b'../init.android',b'/init.android')
assert 'lib/modules/galcore.ko' not in parsed
assert b'/stage-data/local/tmp/t110-lineage14-system.raw' in stage
assert b'--second-stage' in stage and b'/init.android' in stage
packed_ramdisk=gzip.compress(raw,mtime=0)
old=BOOT48.read_bytes();assert hashlib.sha256(old).hexdigest()=='09da369cd22d09e1b59b70ce273fa305c96cc83bc83bca8a48132737763d3690'
kernel=(DEVICE/'prebuilt/zImage').read_bytes();assert hashlib.sha256(kernel).hexdigest()==json.loads((DEVICE/'kernel-source.json').read_text())['kernel_sha256']
page=struct.unpack_from('<I',old,36)[0];assert page==2048
assert struct.unpack_from('<I',old,24)[0]==0,'Unexpected second boot payload'
assert struct.unpack_from('<I',old,40)[0]==0,'Unexpected separate device-tree payload'
header=bytearray(old[:page]);struct.pack_into('<I',header,8,len(kernel));struct.pack_into('<I',header,16,len(packed_ramdisk))
cmdline=old[64:576].split(b'\0',1)[0].decode()
assert len(cmdline.encode())<512
header[64:576]=cmdline.encode().ljust(512,b'\0')
digest=hashlib.sha1()
for payload in (kernel,packed_ramdisk,b''):
    digest.update(payload);digest.update(struct.pack('<I',len(payload)))
header[576:608]=digest.digest()+bytes(12)
align=lambda b:b+bytes(-len(b)%page)
boot=bytes(header)+align(kernel)+align(packed_ramdisk)
assert len(boot)<BOOT_SIZE
assert boot[page:page+len(kernel)]==kernel
assert gzip.decompress(boot[page+len(align(kernel)):page+len(align(kernel))+len(packed_ramdisk)])==raw
(DEST/'boot.img').write_bytes(boot.ljust(BOOT_SIZE,b'\0'))
system=OUT/'system.img'
assert system.is_file()
with system.open('rb') as source:
    sparse_magic=source.read(4)
if args.reuse_system:
    assert args.reuse_system_sha256 and hashlib.sha256(args.reuse_system.read_bytes()).hexdigest()==args.reuse_system_sha256
    assert args.reuse_system.stat().st_size==SYSTEM_SIZE
    if args.reuse_system.resolve()!=(DEST/'system.raw.img').resolve():shutil.copy2(args.reuse_system,DEST/'system.raw.img')
elif sparse_magic==b'\x3a\xff\x26\xed':
    subprocess.run(['simg2img',str(system),str(DEST/'system.raw.img')],check=True)
else:shutil.copy2(system,DEST/'system.raw.img')
assert (DEST/'system.raw.img').stat().st_size==SYSTEM_SIZE
check=subprocess.run(['e2fsck','-fn',str(DEST/'system.raw.img')],capture_output=True,text=True)
fslog=check.stdout+check.stderr
normalized_padding=False
if check.returncode!=0:
    # Old Android make_ext4fs leaves unused final inode-bitmap padding clear.
    # Normalize only this identified issue in the generated copy; input is untouched.
    questions=[line for line in fslog.splitlines() if 'Fix?' in line]
    if check.returncode!=4 or questions!=['Padding at end of inode bitmap is not set. Fix? no']:
        (DEST/'filesystem-check.txt').write_text(fslog)
        raise RuntimeError('Unexpected system filesystem verification failure')
    repair=subprocess.run(['e2fsck','-fy',str(DEST/'system.raw.img')],capture_output=True,text=True)
    fslog+='\nGenerated-copy bitmap padding normalization:\n'+repair.stdout+repair.stderr
    if repair.returncode not in (0,1):raise RuntimeError('Bitmap padding normalization failed')
    check=subprocess.run(['e2fsck','-fn',str(DEST/'system.raw.img')],capture_output=True,text=True)
    fslog+='\nFinal read-only check:\n'+check.stdout+check.stderr
    normalized_padding=True
(DEST/'filesystem-check.txt').write_text(fslog)
if check.returncode!=0:raise RuntimeError('Final system filesystem verification failed')
# Keep the recovered startup/graphics lessons in the mandatory packaging gate.
# This checks the actual packed ramdisk and ext4, including dynamic driver paths
# that a DT_NEEDED-only dependency check cannot see.
subprocess.run(['python3',str(Path(__file__).with_name('verify_prior_graphics_fixes.py'))],check=True)
subprocess.run(['python3',str(Path(__file__).with_name('verify_final_image.py'))],check=True)
report={'status':'BUILT_OFFLINE_VERIFIED_NOT_HARDWARE_TESTED','android':'7.1.2','lineage':'14.1',
        'physical_system_write_allowed':False,'system_destination':'/data/local/tmp/t110-lineage14-system.raw',
        'userdata_directory':'/data/local/tmp/t110-lineage14-data','kernel':'v42 plus GOYA initramfs archive-end fix; original config/module ABI',
        'selinux':'permissive bring-up; not a production security qualification',
        'reused_verified_system':bool(args.reuse_system),'google_apps_included':False,'inode_bitmap_padding_normalized':normalized_padding,'vendor_elfs_verified':len(elf_report['files']),'files':[]}
for name in ('boot.img','system.raw.img'):
    p=DEST/name
    with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest() if hasattr(hashlib,'file_digest') else None
    if digest is None:
        h=hashlib.sha256()
        with p.open('rb') as f:
            while data:=f.read(1024*1024):h.update(data)
        digest=h.hexdigest()
    report['files'].append({'name':name,'bytes':p.stat().st_size,'sha256':digest})
(DEST/'build-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
