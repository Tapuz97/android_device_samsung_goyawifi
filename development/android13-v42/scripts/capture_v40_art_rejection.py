"""Capture why ART prefers the old extracted cache over the new prebuilt."""
from pathlib import Path
import os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112/v40-ui'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
commands={
    'art-rejection-log':'logcat -d -b all -t 6000',
    'art-rejection-paths':'ls -lZ /system/product/priv-app/Velvet/oat/arm; ls -l /apex/com.android.art/bin/oatdump; ls -l /data/dalvik-cache/arm/system@product@priv-app@Velvet@Velvet.apk*; getprop dalvik.vm.isa.arm.variant; getprop dalvik.vm.isa.arm.features; pidof com.google.android.googlequicksearchbox',
    'art-header':'/apex/com.android.art/bin/oatdump --oat-file=/system/product/priv-app/Velvet/oat/arm/Velvet.odex --header-only',
    'art-package':'dumpsys -t 30 package com.google.android.googlequicksearchbox',
}
for name,command in commands.items():
    r=subprocess.run(adb+['shell',command],capture_output=True,timeout=90)
    text=(r.stdout+r.stderr).decode(errors='replace').replace('\r','');(e/(name+'.txt')).write_text(text,encoding='utf-8')
    if name in ['art-rejection-paths','art-header']:print(name+'\n'+text[:4500])
    if name=='art-rejection-log':
        print('\n'.join(line for line in text.splitlines() if any(x in line.lower() for x in ['oatfile','classloadercontext','checksum','velvet.odex','dex2oat','oat file']))[-5000:])
