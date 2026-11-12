"""Stop the failed adapter trial and retain a verified, non-rebooted resume state."""
from pathlib import Path
import datetime,json,os,re,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=45,check=True):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
 if check:assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')[-2000:]
 return r.stdout.decode(errors='replace').strip()
install=json.loads((e/'v38-installation.json').read_text());boot=sh('cat /proc/sys/kernel/random/boot_id');assert boot==install['boot_id']
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
server=sh('pidof system_server');netd=sh('pidof netd');assert server==install['system_server'] and netd
disabled=sh('cmd bluetooth_manager disable',check=False);(e/'blocked-disable.txt').write_text(disabled+'\n',encoding='utf-8')
result=dict(host_time=datetime.datetime.now().astimezone().isoformat(),system_revision=38,boot_revision=45,boot_id=boot,
 system_server=server,netd=netd,system_sha256=install['system_sha256'],boot_sha256=install['boot_sha256'],
 selinux=sh('getenforce'),gpu_flag=sh('getprop debug.hwui.t110_window_gpu'),bluetooth_functional=False,
 bluetooth_temporarily_disabled=True,controller_identity_mode_corrected_live=True,new_boots_during_checkpoint=0,
 pending_revision=39,pending_build_reported_success=True,pending_image_verified=False,pending_fixes_installed=False,
 blocker='E disappeared after disk153 read retry; native build succeeded but new binaries not exported',physical_system_written=False,recovery_written=False,data_profiles_preserved=True)
for action in ['https','storage']:
 text=sh('am instrument --no-hidden-api-checks -w -e action '+action+' dev.tapuz.t110.interaction/.InteractionInstrumentation',120)
 (e/('blocked-app-'+action+'.txt')).write_text(text+'\n',encoding='utf-8');match=re.search(r'INSTRUMENTATION_RESULT: report=(.*)',text);assert match
 result[action]=json.loads(match[1])
result['boot_server_netd_stable']=sh('cat /proc/sys/kernel/random/boot_id')==boot and sh('pidof system_server')==server and sh('pidof netd')==netd
result['wifi_dns_tls_pass']=result['https'].get('completed') and result['https'].get('https_code')==204 and result['https'].get('validated')
result['microsd_roundtrips']=result['storage'].get('storage',{}).get('removable_roundtrips_passed',0)
(e/'blocked-final-status.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['system_revision','boot_revision','boot_server_netd_stable','wifi_dns_tls_pass','microsd_roundtrips','blocker']},indent=2))
