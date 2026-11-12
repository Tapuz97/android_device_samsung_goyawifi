from pathlib import Path
import os,re,subprocess,time,sys
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def run(command,timeout=45):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout);return r.returncode,(r.stdout+r.stderr).decode(errors='replace')
for cmd in ['cmd bluetooth_manager disable','cmd bluetooth_manager wait-for-state:STATE_OFF','cmd bluetooth_manager enable','cmd bluetooth_manager wait-for-state:STATE_ON']:
 if '--capture-only' in sys.argv:break
 code,text=run(cmd,45);print(cmd,code,text.strip(),flush=True)
if '--capture-only' not in sys.argv:time.sleep(10)
for name,cmd in {'enable-after-mode-manager':'dumpsys bluetooth_manager','enable-after-mode-log':'logcat -d -b all -t 5000','enable-after-mode-state':'am instrument --no-hidden-api-checks -w -e action bluetooth -e stateOnly true dev.tapuz.t110.interaction/.InteractionInstrumentation'}.items():
 code,text=run(cmd,90);(e/(name+'.txt')).write_text(text,encoding='utf-8')
 if name.endswith('manager'):print('\n'.join(line for line in text.splitlines() if re.search(r'enabled:|state:|crashed',line)))
 if name.endswith('state'):print(text)
 if name.endswith('log'):
  print('\n'.join(line for line in text.splitlines() if any(x in line for x in ['Abort message:','get_local_address: Error','get_local_address: Got Invalid','Firmware configured','hci_layer.cc:']) and not 'Got Invalid' in line)[-5000:])
