from pathlib import Path
import json,os,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112';adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
commands={'velvet-profiles':'unzip -l /system/product/priv-app/Velvet/Velvet.apk',
 'profile-files':'ls -l /data/misc/profiles/ref/com.google.android.googlequicksearchbox /data/misc/profiles/cur/0/com.google.android.googlequicksearchbox /data/misc/profiles/ref/com.google.android.gms /data/misc/profiles/cur/0/com.google.android.gms',
 'velvet-package':'dumpsys package com.google.android.googlequicksearchbox'}
for name,command in commands.items():
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=45);text=(r.stdout+r.stderr).decode(errors='replace');(e/(name+'.txt')).write_text(text,encoding='utf-8')
 if name=='velvet-profiles':print('APK PROFILES\n'+'\n'.join(line for line in text.splitlines() if 'assets/dexopt' in line))
 elif name=='profile-files':print(text)
 else:print('PROFILE RECEIVER\n'+'\n'.join(line for line in text.splitlines() if 'profileinstaller' in line.lower()))
