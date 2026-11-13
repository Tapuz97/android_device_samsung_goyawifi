"""Verify actual ARM32 HAL layouts and preserved kernel/driver input identities."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tempfile

ROOT=Path('/root/t110-lineage14')
ANDROID=ROOT/'android'
DEVICE=ANDROID/'device/samsung/goyawifi'
COMPILER=ANDROID/'prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-gcc'
names=['sizeof(hwc_layer_1_t)','offsetof(hwc_layer_1_t,sourceCrop)',
       'offsetof(hwc_layer_1_t,displayFrame)','offsetof(hwc_layer_1_t,visibleRegionScreen)',
       'offsetof(hwc_layer_1_t,acquireFenceFd)','offsetof(hwc_layer_1_t,planeAlpha)',
       'sizeof(hwc_composer_device_1_t)','offsetof(hwc_composer_device_1_t,getDisplayAttributes)',
       'offsetof(hwc_composer_device_1_t,fbPrePost)']
values=[100,28,44,60,68,76,116,96,100]
names += ['sizeof(hwc_display_contents_1_t)','offsetof(hwc_display_contents_1_t,retireFenceFd)',
          'offsetof(hwc_display_contents_1_t,dpy)','offsetof(hwc_display_contents_1_t,sur)',
          'offsetof(hwc_display_contents_1_t,flags)','offsetof(hwc_display_contents_1_t,numHwLayers)',
          'offsetof(hwc_display_contents_1_t,hwLayers)']
values += [20,0,4,8,12,16,20]
source='#include <stddef.h>\n#include <hardware/hwcomposer.h>\n'
source+='\n'.join('typedef char check%d[(%s == %d) ? 1 : -1];'%(i,n,v) for i,(n,v) in enumerate(zip(names,values)))+'\n'
with tempfile.TemporaryDirectory(prefix='t110-arm-abi-') as tmp:
    p=Path(tmp);(p/'check.c').write_text(source)
    for name,headers,macro in [('stock',ROOT/'reference/t110-libhardware/include','MRVL_HARDWARE'),('nougat',ANDROID/'hardware/libhardware/include','T110_MRVL_LEGACY')]:
        includes=[headers,ANDROID/'system/core/include',ANDROID/'bionic/libc/include',
                  ANDROID/'bionic/libc/arch-arm/include',ANDROID/'bionic/libc/kernel/uapi',
                  ANDROID/'bionic/libc/kernel/uapi/asm-arm']
        cmd=[str(COMPILER),'-c','-std=gnu11','-D'+macro]
        cmd+=['-I'+str(x) for x in includes]+[str(p/'check.c'),'-o',str(p/(name+'.o'))]
        subprocess.run(cmd,check=True)
        header=subprocess.check_output(['readelf','-h',str(p/(name+'.o'))],text=True)
        assert 'ARM' in header and 'ELF32' in header
report={'status':'INPUTS_AND_ARM32_ABI_VERIFIED','layout':dict(zip(names,values)),'modules':[]}
for path in sorted((DEVICE/'prebuilt').iterdir()):
    if path.is_file():
        data=path.read_bytes();item={'name':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        if path.suffix=='.ko':
            assert data[:6]==b'\x7fELF\1\1'
            metadata=subprocess.check_output(['readelf','-p','.modinfo',str(path)],text=True)
            item['vermagic']=re.search(r'vermagic=(.*)',metadata).group(1).strip()
        report['modules'].append(item)
assert next(x for x in report['modules'] if x['name']=='zImage')['sha256']==json.loads((DEVICE/'kernel-source.json').read_text())['kernel_sha256']
assert len({x['vermagic'] for x in report['modules'] if 'vermagic' in x})==1
for name,expected in [('gralloc.mrvl.so','da8e8887f877d5de012500cd390127742a68fb8b3b53d39b4560712f0c393c58'),('hwcomposer.mrvl.so','66b02de15b357fb5127846f89288f81aebf5b93701e3d7c999b60922190f1f6f')]:
    assert hashlib.sha256((DEVICE/'proprietary/lib/hw'/name).read_bytes()).hexdigest()==expected
records=ROOT/'records';records.mkdir(exist_ok=True)
(records/'input-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('Both actual ARM32 compile probes passed all sixteen layout assertions.')
print('Preserved kernel hash, matched graphics hashes, and all four module vermagic strings passed.')
