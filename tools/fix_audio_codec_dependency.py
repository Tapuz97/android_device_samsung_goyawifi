"""Declare ANI7 libacm's implicit MD5 dependency through Lineage's linker hook."""
from pathlib import Path
p = Path('/root/t110-lineage14/android/device/samsung/goyawifi/BoardConfig.mk')
s = p.read_text()
block = '''
# Stock libacm references MD5_Init/Update/Final without a DT_NEEDED provider.
# Only this blob receives the platform crypto dependency; no crypto replacement.
LINKER_FORCED_SHIM_LIBS += /system/vendor/lib/libacm.so|libcrypto.so
'''
if block not in s:
    p.write_text(s + block)
print('Declared exact-path libacm MD5 dependency.')
