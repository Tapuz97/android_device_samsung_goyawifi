"""Retain the compiled repair kernel without repackaging or booting the ROM."""
from pathlib import Path
import hashlib,json,shutil,sys
p=Path(sys.argv[1]);b=Path('/root/t110-build');o=b/'out-display-i2c';src=b/'kernel-display-i2c';e=p/'evidence/offline-v41';a=p/'artifacts/kernel-ion-bounds'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
source=json.loads((e/'ion-mapping-source.json').read_text());test=json.loads((e/'ion-mapping-host-test.json').read_text())
assert test['status']=='PASS' and '37414' in test['output']
assert sha(src/'drivers/gpu/ion/ion_system_heap.c')==source['after_sha256']
assert sha(src/'drivers/gpu/ion/ion.c')=='0b6839e8a4d845a170e23e69c6b5c4489a948816f041d8c267f3a6911330eb8b'
assert sha(src/'drivers/input/touchscreen/bt532_ts.c')=='1a4706eafa67cdf68e5b08ca10c683d07e87910cae439d974715bbf9a0623484'
config=sha(o/'.config');assert config==json.loads((p/'evidence/offline-v34/display-i2c-source.json').read_text())['config_sha256']
modules=list(o.rglob('galcore.ko'));assert len(modules)==1
module_sha=sha(modules[0]);assert module_sha=='0d93682f6a54f51aabfd7c91ab77af0b26c61c86aa8e8519c487c70d7f5c3900'
a.mkdir(exist_ok=False)
for f,name in [(o/'arch/arm/boot/zImage','zImage'),(modules[0],'galcore.ko'),(o/'.config','kernel.config'),(b/'logs/display-i2c-build.log','kernel-build.log')]:shutil.copyfile(f,a/name)
record={'status':'COMPILED_OFFLINE_REGRESSION_PASS_NOT_BOOT_TESTED','kernel_sha256':sha(a/'zImage'),'kernel_bytes':(a/'zImage').stat().st_size,'module_sha256':module_sha,'config_sha256':config,'touch_source_retained':True,'ion_map_ioctl_retained':True,'mapping_bounds_patch':'0081-kernel-goya-bound-ion-user-mappings.patch','host_regression_cases':37414,'old_overrun_reproduced':True,'compiled_for':'ARM32 Cortex-A9, same configuration/toolchain','hardware_decode_passed':False,'new_boot_packaged':False,'flashed':False,'tablet_left':'TWRP'}
(a/'provenance.json').write_text(json.dumps(record,indent=2)+'\n');(e/'ion-bounds-kernel-build.json').write_text(json.dumps(record,indent=2)+'\n')
finding=json.loads((e/'codec-kernel-fault.json').read_text());finding['kernel_build']='PASS';finding['candidate_kernel_sha256']=record['kernel_sha256'];(e/'codec-kernel-fault.json').write_text(json.dumps(finding,indent=2)+'\n')
print(json.dumps(record,indent=2))
