"""Export the compiled import-only fix after source/build/ABI guards."""
from pathlib import Path
import json,subprocess,hashlib
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/remote-fixes-20261110'
b=Path('/root/t110-build');out=b/'out-native';source=b/'lineage20/frameworks/native/libs/ui/Gralloc2.cpp'
tests=json.loads((e/'source-tests.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==tests['source_sha256']['Gralloc2.cpp']
log=(b/'logs/native-bootstrap-20261110T101248Z.log').read_text(errors='replace')
assert 'build completed successfully' in log
f=out/'soong/.intermediates/frameworks/native/libs/ui/libui/android_arm_armv7-a-neon_cortex-a9_shared/libui.so';data=f.read_bytes()
assert data[:5]==b'\x7fELF\x01'
dest=e/'libui-candidate';dest.mkdir(exist_ok=True);(dest/'libui.so').write_bytes(data)
dynamic=subprocess.check_output([str(b/'toolchain/bin/arm-eabi-readelf'),'-d',str(f)],text=True)
(dest/'elf-dynamic.txt').write_text(dynamic)
(dest/'provenance.json').write_text(json.dumps({'status':'COMPILED_NOT_INSTALLED','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sha256':hashlib.sha256(data).hexdigest(),'build_log':'../native-libui-build.log','product':'lineage_t110_bringup-eng','abi':'armv7-a-neon/cortex-a9/binder32','only_libui_source_change_since_v27':'0078 import-only process initialization; 0048 retained allocation owners preserved','full_system_build':False},indent=2)+'\n')
(e/'native-libui-build.log').write_text(log)
print('COMPILED_LIBUI_CANDIDATE_EXPORTED',len(data))
