"""Export successfully compiled lights targets even when the separate SDK target fails."""
from pathlib import Path
import json,hashlib
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');b=Path('/root/t110-build');t=b/'lineage20';out=b/'out-native/soong/.intermediates'
e=p/'evidence/remote-fixes-20261110';dest=e/'lights-candidate';dest.mkdir(exist_ok=True)
assert (p/'work/device/samsung/t110_bringup/lights/lights.c').read_bytes()==(t/'device/samsung/t110_bringup/lights/lights.c').read_bytes()
targets={
 'lights.mrvl.so':'device/samsung/t110_bringup/lights.mrvl/android_arm_armv7-a-neon_cortex-a9_shared/lights.mrvl.so',
 't110_lights_probe':'device/samsung/t110_bringup/t110_lights_probe/android_arm_armv7-a-neon_cortex-a9/t110_lights_probe',
 'android.hardware.light@2.0-service':'hardware/interfaces/light/2.0/default/android.hardware.light@2.0-service/android_vendor.29_arm_armv7-a-neon_cortex-a9/android.hardware.light@2.0-service',
 'android.hardware.light@2.0-impl.so':'hardware/interfaces/light/2.0/default/android.hardware.light@2.0-impl/android_vendor.29_arm_armv7-a-neon_cortex-a9_shared/android.hardware.light@2.0-impl.so',
}
records={}
for name,rel in targets.items():
    f=out/rel
    if not f.exists():
        matches=[x for x in (out/rel.split('/android_')[0]).rglob(name) if '/unstripped/' not in str(x)]
        assert len(matches)==1,(name,matches);f=matches[0]
    data=f.read_bytes();assert data[:5]==b'\x7fELF\x01';(dest/name).write_bytes(data)
    records[name]={'sha256':hashlib.sha256(data).hexdigest(),'source':str(f)}
(dest/'provenance.json').write_text(json.dumps({'status':'COMPILED_NOT_INSTALLED','source_sha256':hashlib.sha256((t/'device/samsung/t110_bringup/lights/lights.c').read_bytes()).hexdigest(),'files':records,'full_sdk_build_passed':False},indent=2)+'\n')
log=(b/'logs/remote-sdk-driver-20261110.log').read_text(errors='replace');(e/'sdk-build-internal-final.log').write_text(log)
print('LIGHTS_SERVICE_ADAPTER_AND_PROBE_COMPILED_EXPORTED')
