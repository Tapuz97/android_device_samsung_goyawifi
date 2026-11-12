from pathlib import Path
import subprocess,json
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
kernel=Path('/root/t110-build/kernel-display-i2c')
module=p/'stock/T110XXUANI7/system/vendor/lib/hw/lights.mrvl.so'
strings=subprocess.check_output(['strings',str(module)],text=True)
(p/'evidence/offline-v41/stock-lights-strings.txt').write_text(strings)
for line in strings.splitlines():
    if any(s in line.lower() for s in ['sys/','button','keyboard','backlight','touchkey','led']): print(line)
config=(Path('/root/t110-build/out-display-i2c/.config')).read_text()
print('\n'.join(s for s in config.splitlines() if 'CONFIG_MFD_88PM' in s or 'CONFIG_MACH_GOYA' in s))
