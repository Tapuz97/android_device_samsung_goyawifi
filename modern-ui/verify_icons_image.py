"""Validate a complete UI image using the original bring-up checks in isolation.

Never overwrites the working ROM, its reports, or anything on the tablet.
"""
from pathlib import Path
import gzip,hashlib,json,shutil,subprocess
BASE=Path('/root/t110-lineage14');WORK=Path('/root/t110-lineage14-ui')
OUT=WORK/'out/target/product/goyawifi';ART=WORK/'artifacts-icons-20261115'
ART.mkdir(exist_ok=True);(WORK/'icons-image-records').mkdir(exist_ok=True)
ORIGINAL=BASE/'artifacts/lineage14-first-build'
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while block:=stream.read(1024*1024):h.update(block)
    return h.hexdigest()
assert digest(ORIGINAL/'system.raw.img')=='01165196d103ecb5939bea6ec367497d956b606ac789178413169fc5f6cb95ea'
assert digest(ORIGINAL/'boot.img')=='93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2'
assert (OUT/'system.img').is_file()
properties=dict(line.split('=',1) for line in (OUT/'system/build.prop').read_text().splitlines()
                if '=' in line and not line.startswith('#'))
assert properties['ro.build.version.incremental']=='T110_UI_20261114_R2',properties['ro.build.version.incremental']
assert properties['ro.bq.gpu_to_cpu_unsupported']=='1'
assert b'ro.bq.gpu_to_cpu_unsupported' in (OUT/'system/lib/libgui.so').read_bytes()
shutil.copy2(ORIGINAL/'boot.img',ART/'boot.img')
with (OUT/'system.img').open('rb') as stream:sparse=stream.read(4)==b'\x3a\xff\x26\xed'
if sparse:subprocess.run(['simg2img',str(OUT/'system.img'),str(ART/'system.raw.img')],check=True)
else:shutil.copy2(OUT/'system.img',ART/'system.raw.img')
assert (ART/'system.raw.img').stat().st_size==1594884096
check=subprocess.run(['e2fsck','-fn',str(ART/'system.raw.img')],capture_output=True,text=True)
log=check.stdout+check.stderr
normalized=False
if check.returncode:
    questions=[line for line in log.splitlines() if 'Fix?' in line]
    assert check.returncode==4 and questions==['Padding at end of inode bitmap is not set. Fix? no'],log
    repair=subprocess.run(['e2fsck','-fy',str(ART/'system.raw.img')],capture_output=True,text=True)
    log+='\nGenerated candidate bitmap padding normalization:\n'+repair.stdout+repair.stderr
    assert repair.returncode in (0,1),log
    check=subprocess.run(['e2fsck','-fn',str(ART/'system.raw.img')],capture_output=True,text=True)
    log+='\nRead-only final check:\n'+check.stdout+check.stderr
    normalized=True
(ART/'filesystem-check.txt').write_text(log)
assert check.returncode==0,log

# Run the existing acceptance gates against this OUT_DIR and artifact directory.
# Keep original source/stock references intact and redirect every output report.
checks=WORK/'icons-image-checks';checks.mkdir(exist_ok=True)
names=['verify_init_service_imports.py','verify_prior_graphics_fixes.py',
       'verify_final_image.py','verify_vendor_elf.py','verify_window_contract_build.py']
source=Path(__file__).parent.parent/'scripts'
if not source.is_dir():source=Path(__file__).parent.parent/'tools'
for name in names:
    original=source/name;text=original.read_text()
    text=text.replace("'artifacts/lineage14-first-build'",repr(str(ART)))
    text=text.replace("'android/out/target/product/goyawifi/system'",repr(str(OUT/'system')))
    text=text.replace("'android/out/target/product/goyawifi/obj/SHARED_LIBRARIES'",repr(str(OUT/'obj/SHARED_LIBRARIES')))
    text=text.replace("'out/target/product/goyawifi'",repr(str(OUT)))
    text=text.replace("'out/host/linux-x86/bin/simg2img'",repr(str(WORK/'out/host/linux-x86/bin/simg2img')))
    text=text.replace("'records/", "'/root/t110-lineage14-ui/icons-image-records/")
    text=text.replace("'records'",repr(str(WORK/'icons-image-records')))
    (checks/name).write_text(text)
    assert (BASE/'artifacts/lineage14-first-build').as_posix() not in text
for name in ('verify_vendor_elf.py','verify_prior_graphics_fixes.py',
             'verify_window_contract_build.py','verify_final_image.py'):
    result=subprocess.run(['python3',str(checks/name)],capture_output=True,text=True)
    (WORK/'logs'/name.replace('.py','.log')).write_text(result.stdout+result.stderr)
    assert result.returncode==0,(name,(result.stdout+result.stderr)[-3000:])
    print('PASS',name,flush=True)

# Verify the actual packaged UI APKs, rather than relying on source edits alone.
aapt=WORK/'out/host/linux-x86/bin/aapt'
resources={
    'priv-app/SystemUI/SystemUI.apk':['t110_qs_tile_background','t110_qs_active'],
    'priv-app/Settings/Settings.apk':['t110_search_settings','t110_settings_icon_background'],
    'app/WallpaperPicker/WallpaperPicker.apk':['lineage_current','lineage_current_small'],
    'priv-app/Trebuchet/Trebuchet.apk':['lineage_current','lineage_current_small']}
for path,required in resources.items():
    result=subprocess.check_output([str(aapt),'dump','resources',str(OUT/'system'/path)],text=True)
    for name in required:assert name in result,(path,name)

with (ART/'system.raw.img').open('rb') as original,(ART/'system.raw.img.gz').open('wb') as output:
    with gzip.GzipFile(fileobj=output,mode='wb',mtime=0) as compressed:shutil.copyfileobj(original,compressed)
report={'status':'OFFLINE_COMPLETE_IMAGE_CHECKS_PASSED_NOT_HARDWARE_QUALIFIED',
        'android':'7.1.2','api':25,'lineage':'14.1','ui_branch':'t110/lineage14-modern-ui-20261114',
        'build_fingerprint':properties['ro.build.fingerprint'],
        'ui_source_manifest_sha256':digest(WORK/'changed-files.json'),
        'boot_reused_unchanged':True,'physical_system_write_allowed':False,
        'inode_bitmap_padding_normalized':normalized,'google_apps_included':False,
        'files':[{'name':name,'bytes':(ART/name).stat().st_size,'sha256':digest(ART/name)}
                 for name in ('boot.img','system.raw.img','system.raw.img.gz')]}
(ART/'ui-image-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
