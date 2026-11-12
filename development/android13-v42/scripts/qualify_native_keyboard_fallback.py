"""Temporarily hide only an unsupported optional Google JNI library, same boot.

The existing LatinIME JniUtils catches dlopen failure and loads its native AOSP
library. This doesn't substitute incompatible ABI symbols or alter the APK.
The final image will omit only this unsupported optional library, not Google apps.
"""
from pathlib import Path
import json,os,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41/gapps-v29-test'
a=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s,timeout=45):return subprocess.check_output(a+['shell',s],timeout=timeout).decode().strip()
before=sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines()
assert before==['dd03b95b-3f7e-4a1e-8c27-84cd94056813','1324']
target='/system/product/lib/libjni_latinimegoogle.so';empty='/data/local/tmp/t110-unsupported-gesture-lib.empty'
assert sh('test ! -e '+empty+' && test ! -L '+empty+' && echo ABSENT')=='ABSENT'
original=sh('sha256sum '+target).split()[0]
assert original=='442a2a8bfcb25489564bc9433a916fa4dc0dba9000fe6f6f03f5939b985091e6'
native='/system/product/lib/libjni_latinime.so'
assert sh('test -f '+native+' && test ! -L '+native+' && readlink -f '+native)==native
native_sha=sh('sha256sum '+native).split()[0]
sh(': > '+empty+' && chmod 0444 '+empty+' && chcon u:object_r:shell_data_file:s0 '+empty)
sh('mount -o bind,ro '+empty+' '+target)
assert sh('stat -c %s '+target)=='0'
record={'status':'LIVE_FALLBACK_QUALIFICATION_IN_PROGRESS','boot_and_server':before,'masked_only':target,'mask_source':empty,
 'original_google_library_sha256':original,'native_keyboard_library':native,'native_keyboard_library_sha256':native_sha,
 'apk_or_physical_system_written':False,'additional_boots':0,'cause':'Google library +0x61520 is SDIV r1,r7,r0; Cortex-A9 has no IDIV support',
 'native_features_preserved':True,'optional_google_gesture_typing_supported':False,'temporary_mount_cleanup_pending':True}
(e/'native-keyboard-fallback.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
