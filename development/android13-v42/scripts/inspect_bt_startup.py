from pathlib import Path
import argparse,os,re,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
parser=argparse.ArgumentParser();parser.add_argument('--label',default='bt-startup');label=parser.parse_args().label;assert re.fullmatch('[a-z0-9-]+',label)
for name,command in {'bt-startup-kernel':'dmesg','bt-startup-init':'cat /init.mrvl.rc; cat /vendor/etc/init/init.t110.bluetooth.rc',
 'bt-startup-state':'getprop init.svc.t110-bluetooth-init; getprop init.svc.t110-radio-init; getprop sys.boot_completed; ls -lZ /dev/mbtchar0; ls -ldZ /data/vendor/t110-bluetooth; pidof system_server; cat /proc/uptime',
 'bt-startup-log':'logcat -d -b all -t 3000'}.items():
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=60);text=(r.stdout+r.stderr).decode(errors='replace')
 (e/(name.replace('bt-startup',label)+'.txt')).write_text(text,encoding='utf-8')
 if name in ('bt-startup-state','bt-startup-init'):print(name,text)
 else:
  print(name)
  print('\n'.join(line for line in text.splitlines() if any(key in line.lower() for key in ['mbt','bluetooth','parse','invalid','t110-radio','t110_bt','firmware']))[-9000:])
