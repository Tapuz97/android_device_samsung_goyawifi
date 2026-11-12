"""Check power/display state and request wake only; preserve this boot and its logs."""
from pathlib import Path
import datetime,json,os,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/v42-owner-unresponsive';e.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
record=dict(time=datetime.datetime.now().astimezone().isoformat(),reboot_requested=False,actions=[])
commands={
 'identity':'cat /sys/block/mmcblk0/device/cid; cat /proc/sys/kernel/random/boot_id; cat /proc/uptime; getprop sys.boot_completed; pidof system_server com.android.systemui',
 'power':'dumpsys -t 10 power',
 'battery':'dumpsys -t 10 battery',
 'last-anr':'dumpsys -t 15 activity lastanr',
}
for name,cmd in commands.items():
 try:
  r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=25);s=(r.stdout+r.stderr).decode(errors='replace').replace('\r','');(e/(name+'.txt')).write_text(s,encoding='utf-8')
  if name=='identity':print(s[:1000],flush=True)
  elif name=='power':print('\n'.join(line for line in s.splitlines() if any(x in line for x in ['mWakefulness=','Display Power:','mScreenBrightnessOverride','mIsPowered='])),flush=True)
  elif name=='battery':print(s[:700],flush=True)
  elif name=='last-anr':print('\n'.join(s.splitlines()[:4]),flush=True)
  record[name+'_exit']=r.returncode
 except subprocess.TimeoutExpired:record[name+'_timeout']=True
r=subprocess.run(adb+['shell','input keyevent KEYCODE_WAKEUP'],capture_output=True,timeout=20)
record['actions'].append(dict(action='WAKEUP_ONLY',exit_code=r.returncode));time.sleep(2)
r=subprocess.run(adb+['shell','dumpsys -t 10 power'],capture_output=True,timeout=20)
s=(r.stdout+r.stderr).decode(errors='replace').replace('\r','');(e/'power-after-wakeup.txt').write_text(s)
print('AFTER WAKE\n'+'\n'.join(line for line in s.splitlines() if 'mWakefulness=' in line or 'Display Power:' in line),flush=True)
(e/'result.json').write_text(json.dumps(record,indent=2)+'\n')
