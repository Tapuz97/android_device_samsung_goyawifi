"""Qualify the native Bluetooth stack, app scans, storage and Wi-Fi on one boot."""
from pathlib import Path
import datetime,json,os,re,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';out=e/'native-qualification-v39.json';assert not out.exists()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=45,check=True):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
 if check:assert r.returncode==0,r.stderr.decode(errors='replace')+r.stdout.decode(errors='replace')
 return r.stdout.decode(errors='replace').strip()
install=json.loads((e/'v39-installation.json').read_text());boot=sh('cat /proc/sys/kernel/random/boot_id')
assert install['boot_id']==boot and sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('getprop sys.boot_completed')=='1' and sh('getenforce')=='Enforcing'
server=sh('pidof system_server');netd=sh('pidof netd');assert server and netd
state=dict(status='STARTED',host_time=datetime.datetime.now().astimezone().isoformat(),boot_id=boot,system_server=server,netd=netd,
 peer_identifiers_exported=False,pairing_tested=False,accessory_audio_tested=False,storage_formatted=False)
def save():out.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
def app(action,state_only=False):
 text=sh('am instrument --no-hidden-api-checks -w -e action '+action+(' -e stateOnly true' if state_only else '')+' dev.tapuz.t110.interaction/.InteractionInstrumentation',150)
 (e/('native-app-'+action+'.txt')).write_text(text+'\n',encoding='utf-8')
 match=re.search(r'INSTRUMENTATION_RESULT: report=(.*)',text);assert match,text[-1500:]
 result=json.loads(match[1]);assert result.get('completed'),result
 return result
save();original_enabled=None
try:
 kernel=sh('dmesg',60);(e/'native-boot-kernel.txt').write_text(kernel+'\n',encoding='utf-8')
 state['vendor_property_trigger_error_absent']='unexported property trigger found: init.svc.t110-radio-init' not in kernel
 state['loader_exit_zero']=bool(re.search(r"Service 't110-bluetooth-init'.*exited with status 0",kernel))
 state['driver_ready_only']=sh('cat /sys/module/mbt8xxx/parameters/require_fw_ready')=='Y'
 node=sh('ls -lZ /dev/mbtchar0');(e/'native-node.txt').write_text(node+'\n')
 state['restricted_node']='t110_bt_device' in node and 'rw-rw----' in node
 state['controller_identity_file_ready']=sh('test -s /data/vendor/t110-bluetooth/controller_address && echo PRESENT')=='PRESENT'
 state['identity_mode_correct']=sh("stat -c '%a %u %g %s' /data/vendor/t110-bluetooth/controller_address")=='640 0 1002 18'
 state['manual_identity_mode_fix_on_this_boot']=json.loads((e/'identity-mode-live-fix.json').read_text())['boot_id']==boot
 state['hal_service_running']=sh('getprop init.svc.vendor.bluetooth-1-1')=='running'
 assert state['loader_exit_zero'] and state['driver_ready_only'] and state['restricted_node'] and state['controller_identity_file_ready'] and state['hal_service_running'] and state['vendor_property_trigger_error_absent'] and state['identity_mode_correct'] and not state['manual_identity_mode_fix_on_this_boot'],state
 help_text=sh('cmd bluetooth_manager help',check=False);(e/'native-manager-help.txt').write_text(help_text+'\n')
 assert 'enable' in help_text and 'disable' in help_text
 first=app('bluetooth',True);state['before']=first
 original_enabled=first['bluetooth']['enabled']
 sh('cmd bluetooth_manager disable')
 sh('cmd bluetooth_manager wait-for-state:STATE_OFF',30)
 off=app('bluetooth',True);state['disabled']=off;assert off['bluetooth']['state']==10,off
 sh('cmd bluetooth_manager enable')
 for attempt in range(18):
  time.sleep(5)
  status=sh('cmd bluetooth_manager wait-for-state:STATE_ON',30,False) if 'wait-for-state:' in help_text else ''
  if 'Success' in status and 'Failed' not in status:break
  manager=sh('dumpsys bluetooth_manager')
  if re.search(r'\bstate:\s*ON\b',manager):break
 scan=app('bluetooth');state['app_scan']=scan
 radio=scan['bluetooth'];assert radio['enabled'] and radio['state_after']==12 and radio['ble_scan_failure']==-1,radio
 assert radio.get('classic_start_return') and radio.get('classic_start_broadcasts',0)>0,radio
 state['classic_discovery_pass']=True;state['ble_scan_request_pass']=radio['ble_scanner_present']
 state['wifi_app']=app('https');network=state['wifi_app']
 assert network.get('wifi_transport') and network.get('validated') and network.get('https_code')==204 and network.get('dns_result_count',0)>0,network
 state['storage_app']=app('storage');state['removable_storage_roundtrips']=state['storage_app']['storage']['removable_roundtrips_passed']
 state['status']='NATIVE_BLUETOOTH_SCANS_WIFI_COEXISTENCE_PASS'
except Exception as error:
 state['status']='NATIVE_QUALIFICATION_FAILED';state['error']=str(error)
 raise
finally:
 if original_enabled is not None:
  try:
   target='enable' if original_enabled else 'disable';target_state='STATE_ON' if original_enabled else 'STATE_OFF'
   sh('cmd bluetooth_manager '+target);sh('cmd bluetooth_manager wait-for-state:'+target_state,30)
   state['after_restore']=app('bluetooth',True)
   state['original_enabled_state_restored']=state['after_restore']['bluetooth']['state']==(12 if original_enabled else 10)
   if not state['original_enabled_state_restored']:state['status']='BLUETOOTH_DISABLE_NOT_CONFIRMED'
  except Exception as error:state['restore_error']=str(error)
 for name,command in {'manager':'dumpsys bluetooth_manager','storage':'sm list-disks; sm list-volumes all; cat /proc/partitions',
                      'services':'service list; lshal', 'errors':"logcat -d -b all -t 4000 | grep -E 'Bluetooth|bluetooth|bt-vendor|avc:.*denied|Fatal signal|FATAL EXCEPTION' || true"}.items():
  try:(e/('native-'+name+'.txt')).write_text(sh(command,90,check=False)+'\n',encoding='utf-8')
  except Exception as error:state[name+'_capture_error']=str(error)
 state['boot_server_netd_stable']=sh('cat /proc/sys/kernel/random/boot_id')==boot and sh('pidof system_server')==server and sh('pidof netd')==netd
 state['selinux']=sh('getenforce')
 if not state['boot_server_netd_stable']:state['status']='PROCESS_STABILITY_FAIL'
 save()
assert state['status']=='NATIVE_BLUETOOTH_SCANS_WIFI_COEXISTENCE_PASS' and state['selinux']=='Enforcing'
print(json.dumps(state,indent=2))
