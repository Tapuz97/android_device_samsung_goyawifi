"""Sync only the reviewed Bluetooth/SD device changes into the build checkout."""
from pathlib import Path
import ctypes,difflib,hashlib,json,os,shutil,subprocess,sys,tempfile
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');tree=Path('/root/t110-build/lineage20');repo=tree/'device/samsung/t110_bringup';local=p/'work/device/samsung/t110_bringup';e=p/'evidence/hardware-bt-sd'
feature=json.loads((e/'controller-features.json').read_text());assert feature['all_three_commands_pass'] and feature['lmp_feature_bit38']
module=json.loads((e/'module-build.json').read_text());data=(e/'mbt8xxx.ko').read_bytes();assert hashlib.sha256(data).hexdigest()==module['module_sha256']
assets=local/'bluetooth/assets';assets.mkdir(exist_ok=True)
if not (assets/'mbt8xxx.ko').exists() or (assets/'mbt8xxx.ko').read_bytes()!=data:(assets/'mbt8xxx.ko').write_bytes(data)
names=['Android.bp','BoardConfig.mk','t110_system.mk','sepolicy/file_contexts','sepolicy/t110_radio_init.te','storage/fstab.mrvl',
 'bluetooth/bt_vendor_t110.c','bluetooth/t110_bt_init.c','bluetooth/init.t110.bluetooth.rc','bluetooth/manifest.xml']
patch=p/'patches/0102-t110-native-bluetooth-and-sd-slot.patch';record=e/'device-source.json'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
refresh='--refresh' in sys.argv
if record.exists() and refresh:
 saved=json.loads(record.read_text())
 for name,expected in saved['files'].items():assert sha(repo/name)==expected,name
 # Recover patch baselines in a private temporary directory. Keep unchanged
 # live source timestamps so a policy-only correction does not restart Soong.
 temp=tempfile.TemporaryDirectory(prefix='t110-device-baseline-',dir='/root/t110-build');baseline=Path(temp.name)
 for name in set(names)|saved['files'].keys():
  if (repo/name).is_file():
   dest=baseline/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/name,dest)
 cmd=['patch','--batch','-R','-p1','-i',str(patch)]
 subprocess.run(cmd+['--dry-run'],cwd=baseline,capture_output=True,check=True)
 subprocess.run(cmd,cwd=baseline,capture_output=True,check=True)
elif refresh:raise AssertionError('Refresh requires an applied source receipt')
if record.exists() and not refresh:
 saved=json.loads(record.read_text())
 for name in names:assert sha(repo/name)==saved['files'][name]==sha(local/name),name
else:
 assert refresh or not patch.exists();chunks=[]
 for name in names:
  f=(baseline if refresh else repo)/name;before=f.read_text() if f.exists() else '';after=(local/name).read_text()
  if before!=after:chunks.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),('a/'+name) if before else '/dev/null','b/'+name))
 patch.write_text(''.join(chunks))
 for name in names:
  dest=repo/name;dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists() or dest.read_bytes()!=(local/name).read_bytes():shutil.copyfile(local/name,dest)
 (repo/'bluetooth/assets').mkdir(exist_ok=True)
 if not (repo/'bluetooth/assets/mbt8xxx.ko').exists() or (repo/'bluetooth/assets/mbt8xxx.ko').read_bytes()!=data:shutil.copyfile(assets/'mbt8xxx.ko',repo/'bluetooth/assets/mbt8xxx.ko')
 record.write_text(json.dumps(dict(files={name:sha(repo/name) for name in names},module_sha256=module['module_sha256'],patch_sha256=sha(patch)),indent=2)+'\n')
 if refresh:temp.cleanup()
lines=[line.split() for line in (local/'storage/fstab.mrvl').read_text().splitlines() if line and not line.startswith('#')]
sd=next(line for line in lines if 'voldmanaged=sdcard1:auto' in line[-1]);assert len(sd)==5
libc=ctypes.CDLL(None);libc.fnmatch.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int];libc.fnmatch.restype=ctypes.c_int
checks={
 '/devices/platform/sdhci-pxav3.0/mmc_host/mmc1/mmc1:abcd/block/mmcblk1':True,
 '/devices/platform/sdhci-pxav3.0/mmc_host/mmc1/mmc1:0001/block/mmcblk1/mmcblk1p1':True,
 '/devices/platform/sdhci-pxav3.2/mmc_host/mmc0/mmc0:0001/block/mmcblk0':False,
 '/devices/platform/sdhci-pxav3.1/mmc_host/mmc2/mmc2:0001/mmc2:0001:1':False,
 '/devices/platform/sdhci-pxav3.0/mmc_host/mmc10/mmc10:0001/block/mmcblk1':False,
}
for path,expected in checks.items():assert (libc.fnmatch(sd[0].encode(),path.encode(),0)==0)==expected,path
(e/'sd-slot-path-checks.json').write_text(json.dumps(dict(pattern=sd[0],passed=len(checks),kernel_vfat=True,kernel_exfat=False,physical_card_test='PENDING'),indent=2)+'\n')
print('DEVICE_BLUETOOTH_AND_SD_SYNCED_PATH_CHECKS_PASS',len(checks))
