"""Reconcile the installed BT/SD result without changing the frozen baseline."""
from pathlib import Path
from collections import Counter
import datetime,json,os,re,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd'
install=json.loads((e/'v38-installation.json').read_text());q=json.loads((e/'native-qualification.json').read_text())
assert q['status']=='NATIVE_BLUETOOTH_SCANS_WIFI_COEXISTENCE_PASS' and q['boot_server_netd_stable'] and q['selinux']=='Enforcing'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=30,check=True);return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('cat /proc/sys/kernel/random/boot_id')==install['boot_id']==q['boot_id']
assert sh('pidof system_server')==q['system_server'] and sh('pidof netd')==q['netd']
assert sh('getprop debug.hwui.t110_window_gpu')=='false' and sh('getenforce')=='Enforcing'
host=json.loads((p/'artifacts/lineage20-rom-v38-gapps/host-verification.json').read_text())
state=dict(host_time=datetime.datetime.now().astimezone().isoformat(),system_revision=38,boot_revision=45,
 system_sha256=install['system_sha256'],boot_sha256=install['boot_sha256'],boot_id=install['boot_id'],system_server=q['system_server'],netd=q['netd'],
 bluetooth_native_enable_discovery_ble_request_disable_pass=True,bluetooth_pairing_tested=False,bluetooth_audio_tested=False,
 wifi_app_dns_tls_validated_pass=True,microsd_roundtrips=q['removable_storage_roundtrips'],
 microsd_status='PASS' if q['removable_storage_roundtrips'] else 'PENDING_PHYSICAL_CARD',
 kernel_unchanged_from_boot42=True,selinux='Enforcing',native_and_google_components_retained=host['all_native_and_google_components_retained'],
 data_profiles_preserved=True,physical_system_written=False,recovery_written=False,ui_smoothness_pass=False,normal_gpu_windows_qualified=False,
 seconds_to_boot_completed=install['seconds_to_boot_completed'])
(e/'final-status.json').write_text(json.dumps(state,indent=2)+'\n')
link='evidence/hardware-bt-sd/native-qualification.json'
updates={
 'CORE01':('PARTIAL',f"v38/BOOT45 reaches Android boot_completed in {state['seconds_to_boot_completed']} seconds. Native Bluetooth and ordinary-app networking run; this is not a launcher responsiveness qualification.",link),
 'NET10':('PASS','The restricted mbt8xxx driver loads automatically, the controller identity is read without programming it, and the standard Android Bluetooth HAL/manager provides an enabled adapter. SELinux remains Enforcing.',link),
 'NET11':('PASS','Native manager enable/disable and ordinary-app classic discovery passed. BLE scan requests are accepted without errors. Original enabled state restored; system_server/netd/boot identity stayed stable. This is not a pairing or audio pass.',link),
 'NET12':('PENDING_PHYSICAL','The native adapter/discovery path is available. Real peer pairing, reconnect and bond persistence need an owner accessory; no pairing was invented.',link),
 'NET13':('BLOCKED','The native Bluetooth provider is installed, but real accessory audio is untested and the speaker/microphone audio port is unfinished. SCO and hardware offload requests explicitly fail as unsupported.',link),
 'NET14':('PARTIAL','BLE controller capability and ordinary-app scan requests pass. Actual BLE peer traffic, HID and file transfers still require accessory/profile tests.',link),
 'HW09':('PASS' if state['microsd_roundtrips'] else 'PENDING_PHYSICAL',
   'Normal vold microSD configuration is installed. A removable card passed the app-private 64 KiB write/fsync/read/remove test; no formatting performed.' if state['microsd_roundtrips'] else
   'Normal vold microSD configuration is installed for the actual mmc1 slot. No card is currently mounted, so detection and write/read remain pending. VFAT/FUSE kernel support is present; exFAT is not qualified. No formatting performed.',link),
}
f=p/'FUNCTIONAL-CHECKLIST.md';lines=f.read_text(encoding='utf-8').splitlines()
for i,line in enumerate(lines):
 match=re.match(r'- \[[ x]\] \*\*([A-Z]+\d+) (.*?) - [A-Z_]+\*\*\.',line)
 if match and match[1] in updates:
  status,description,url=updates.pop(match[1]);lines[i]=f'- [{"x" if status=="PASS" else " "}] **{match[1]} {match[2]} - {status}**. {description} [evidence]({url})'
assert not updates,updates
text='\n'.join(lines)+'\n';counts=Counter(re.findall(r'^- \[[ x]\] \*\*[^\n]* - ([A-Z_]+)\*\*\.',text,re.M))
text=re.sub(r'^Counts: .*$', 'Counts: '+', '.join(f'{key}={value}' for key,value in sorted(counts.items()))+'.',text,flags=re.M)
text=text.replace('[Current hardware checkpoint](evidence/hardware-v35/v36-final-status.json)','[Current hardware checkpoint](evidence/hardware-bt-sd/final-status.json)')
f.write_text(text,encoding='utf-8')
current=p/'CURRENT-STATUS.md';text=current.read_text(encoding='utf-8')
text=text.replace('Updated2026-11-11. System v36-GApps and BOOT42 are installed.','Updated2026-11-12. System v38-GApps and BOOT45 are installed.')
text=text.replace('## Verified current result','''## Current Bluetooth and microSD result

Native Bluetooth loader, HAL/manager, enable/disable and ordinary-app classic
discovery pass. BLE scan requests are accepted without errors; real BLE peer
traffic remains untested. Wi-Fi DNS/HTTPS204 remains VALIDATED during the check.
Controller identity is preserved. All four H4 transport regressions pass on ARM.
The matching boot image retains BOOT42's kernel and updates policy, SD fstab and
restricted Bluetooth node ownership. SELinux remains Enforcing. Data profiles,
Lineage/Google components and TWRP are retained. Reverse deltas remain available.

MicroSD native vold configuration is installed; physical card mounting/read-write
is separate and reflected in evidence/hardware-bt-sd/final-status.json.
Pairing, accessory audio and HID still require real peers. This is not a claim
that all Bluetooth profiles, hardware audio or exFAT work.

Read HARDWARE-BT-SD.md, evidence/hardware-bt-sd/final-status.json and
native-qualification.json. The source/build/image/boot/install receipts are in
the same folder. Do not rerun their one-shot installers. No build/test is running
after this checkpoint.

## Previously verified v36 baseline''')
old='''- Bluetooth H4 transport source and SDIO identity match mbt8xxx; no module/HAL
  integration yet. Read BLUETOOTH-TRANSPORT-NOTES.md before loading anything;
  driver0666 policy must not enter production. Camera raw capture passed earlier,
  but Android provider, audio, sensors and capacitive-key LEDs remain unfinished.'''
new='''- Bluetooth native adapter/discovery integration now passes; real pairing/audio,
  BLE traffic and HID remain physical/profile checks. Camera raw capture passed
  earlier, but Android provider, audio, sensors and capacitive-key LEDs remain
  unfinished. MicroSD needs a real card; do not format owner media.'''
assert old in text;text=text.replace(old,new)
text=text.replace('BOOT42 unchanged by v36. Reverse delta is retained on the tablet.','BOOT45 is paired with v38. Verified reverse updates are retained on the tablet.')
current.write_text(text,encoding='utf-8')
workspace=p/'BUILD-WORKSPACE.json';data=json.loads(workspace.read_text())
data.update(state='v38-GApps / BOOT45 installed; native Bluetooth scanning and Wi-Fi coexistence pass',phase='HARDWARE_FUNCTIONAL_REPAIRS',
 output='T110Build:/root/t110-build/out-system',installed_system_version=38,installed_boot_version=45,
 installed_system_sha256=state['system_sha256'],installed_boot_sha256=state['boot_sha256'],current_hardware_checkpoint='evidence/hardware-bt-sd/final-status.json',
 pending_boot_artifact=None,pending_boot_sha256=None,pending_boot_status=None,pending_system_artifact=None,pending_system_sha256=None,
 full_build_blocker=None,active_build_session=None,active_test_session=None,active_stage_session=None,development_paused=False)
workspace.write_text(json.dumps(data,indent=2)+'\n')
(p/'RESUME-NEXT.md').write_text('''# Resume hardware development — v38-GApps / BOOT45

Read CURRENT-STATUS.md, FUNCTIONAL-CHECKLIST.md, HARDWARE-BT-SD.md and
evidence/hardware-bt-sd/final-status.json. Exact current hashes and boot identity
are in v38-installation.json. No build/test is left running. Keep native Lineage
and Google features. Verified ready fixes may be built/flashed automatically.

1. Bluetooth native adapter/discovery and Wi-Fi coexistence are verified.
   Real pairing, bond reconnect, BLE peer traffic and HID need accessories.
   Audio remains unported. Do not repeat raw HCI probes while Android owns HCI.
2. MicroSD has normal vold configuration for the actual mmc1 external slot.
   Ask for/inventory a real card, detect/mount read-only first, then use only the
   app-private temporary-file test. No formatting or adoption. exFAT unqualified.
3. Continue camera provider/output, real audio, sensors and stock-working key
   LEDs using their existing source/evidence. No guessed regulator writes.
4. GPU windows remain unqualified: full-size simple fixtures passed but real
   Settings misses labels and corrupts its top. Keep t110_window_gpu=false until
   real native UI pixel/lifecycle checks pass. UI lag/startup ANRs remain open.
5. Wi-Fi ordinary-app DNS/TLS and reconnect pass. Legacy station metrics need
   a separate fix preserving unavailable counters rather than inventing zeroes.

Never write physical SYSTEM/mmcblk0p15. The active system is a userdata loop file;
paired reverse deltas and BOOT42 are retained. Both data profiles/TWRP preserved.
Do not rerun old installers. Linux source/output live in T110Build on E; the
qualified kernel/toolchain are in Ubuntu on C. SSD checks this run found no new
129/153 events. Keep active files in place; delete obsolete outputs only when
identified, never move clutter to another drive.

Source patches0100–0104 and build/transport receipts are documented. Existing
community PRs remain in community/contributions.json. No public ROM release or
new Gerrit submission is claimed. XDA publication waits for the release gates.
''',encoding='utf-8')
print(json.dumps(state,indent=2));print('CHECKLIST_COUNTS',dict(sorted(counts.items())))
