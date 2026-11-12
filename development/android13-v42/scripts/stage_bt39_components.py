"""Keep the build session alive and export the small verified payload immediately."""
from pathlib import Path
import hashlib,json,os,struct,time
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/hardware-bt-sd';dest=e/'v39-components';dest.mkdir(exist_ok=True);manifest=dest/'manifest.json';assert not manifest.exists()
root=Path('/root/t110-build/lineage20');product=Path('/root/t110-build/out-system/target/product/t110_bringup')
log=Path((e/'lookup-build-log.txt').read_text().strip());deadline=time.monotonic()+1200
while True:
 data=log.read_bytes()
 if b'ninja failed with:' in data:raise RuntimeError('Native component build failed; no payload exported')
 if b'build completed successfully' in data:break
 if time.monotonic()>deadline:raise TimeoutError('No successful component build in the bounded export window')
 time.sleep(1)
assert b'\0' not in data,'Build log contains lost or corrupt data'
guard=json.loads((e/'lookup-watchdog-source.json').read_text());device=json.loads((e/'device-source.json').read_text());sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha((root/'packages/modules/Bluetooth'/guard['file']).read_bytes())==guard['after_sha256']
assert sha((root/'device/samsung/t110_bringup/bluetooth/t110_bt_init.c').read_bytes())==device['files']['bluetooth/t110_bt_init.c']
files={}
for number,name in enumerate(['system/vendor/bin/t110_bt_init','system/apex/com.android.btservices/lib/libbluetooth_jni.so']):
 source=product/name;payload=source.read_bytes();assert payload[:6]==b'\x7fELF\1\1' and struct.unpack_from('<H',payload,18)[0]==40
 if number==0:assert b'fchmod\0' in payload
 f=dest/f'component-{number}.elf';assert not f.exists()
 with f.open('wb') as stream:stream.write(payload);stream.flush();os.fsync(stream.fileno())
 assert sha(f.read_bytes())==sha(payload);files[name]=dict(file=f.name,sha256=sha(payload),bytes=len(payload))
saved=dest/'native-build.log'
with saved.open('wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
record=dict(status='NATIVE_COMPONENTS_EXPORTED_VERIFIED',build_log=str(log),saved_build_log_sha256=sha(data),watchdog_source=guard,device_source=device,files=files)
temp=dest/'manifest.incoming'
with temp.open('w') as stream:stream.write(json.dumps(record,indent=2)+'\n');stream.flush();os.fsync(stream.fileno())
temp.rename(manifest);print('V39_COMPONENTS_SAVED_AND_HASHED_ON_INTERNAL_DRIVE',flush=True)
