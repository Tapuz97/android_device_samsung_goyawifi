"""Reconcile current qualification evidence with the live tablet and checklist."""
from pathlib import Path
from collections import Counter
import datetime,hashlib,json,os,re,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35'
install=json.loads((e/'netd-event/v36-installation.json').read_text())
network=json.loads((e/'v36-wifi-reconnect.json').read_text());speed=json.loads((e/'v36-systemui-speed.json').read_text())
assert network['app_dns_tls_pass'] and network['automatic_reconnection'] and network['netd_stable'] and network['boot_and_server_stable']
assert speed['profile_exit']==0 and speed['boot_server_netd_stable']
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=45):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout);assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('cat /proc/sys/kernel/random/boot_id')==install['boot_id']
assert sh('getprop debug.hwui.t110_window_gpu')=='false' and sh('settings get global stay_on_while_plugged_in')=='0'
assert sh('sha256sum /system/bin/netd').split()[0]==json.loads((e/'netd-event/compiled.json').read_text())['netd_sha256']
for name in ['enable_gpu_debug_layers','gpu_debug_app','gpu_debug_layers_gles','gpu_debug_layer_app']:
 assert sh('settings get global '+name)=='null',name
assert sh('pidof system_server')==network['system_server'] and sh('pidof netd')==network['netd']
gpu_path=e/'v36-settings-gpu.json';gpu=json.loads(gpu_path.read_text())
assert gpu['gpu_flag_restored'] and gpu['stay_on_restored']
gpu['visual_review']=dict(status='FAIL_TEXT_AND_TOP_EDGE_CORRUPTION',image='hardware-tests/20261109-settings-wallpaper/v36-normal-gpu.png',
 finding='Settings vectors/background draw; labels are missing and white strips corrupt the top. Offscreen primitive passes did not qualify normal application rendering.')
gpu_path.write_text(json.dumps(gpu,indent=2)+'\n',encoding='utf-8')
state=dict(host_time=datetime.datetime.now().astimezone().isoformat(),system_revision=36,boot_revision=42,
 boot_id=install['boot_id'],system_sha256=install['system_sha256'],boot_sha256=install['boot_sha256'],
 system_server=network['system_server'],netd=network['netd'],selinux=sh('getenforce'),wifi_enabled='Wifi is enabled' in sh('cmd wifi status'),
 wifi_cycle_dns_tls_pass=True,normal_gpu_window_qualification='FAIL_TEXT_CORRUPTION',software_settings_draw_and_scroll_pass=True,
 ui_smoothness_pass=False,systemui_compiled_speed=True,startup_anrs_fixed=False,bluetooth_functional=False,camera_functional=False,
 gpu_flag='false',debug_layers_restored=True,stay_on_restored=True,recovery_written=False,physical_system_written=False,data_profiles_preserved=True)
(e/'v36-final-status.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
updates={
'CORE01':('PARTIAL','v36/BOOT42 reaches unlocked Android in227.76s. Native Settings subsequently draws and scrolls; current full launcher qualification is pending. Startup success is not a responsiveness pass.','evidence/hardware-v35/netd-event/v36-installation.json'),
'CORE02':('FAIL','The netd-triggered Android restart is fixed and process stability passed a real Wi-Fi cycle. Separate SystemUI/Google startup ANRs and long startup remain.','evidence/hardware-v35/v36-safe-ui-qualification.json'),
'CORE08':('PARTIAL','Earlier lifecycle/navigation baseline passed. The current build had focus ANRs; after native SystemUI speed compilation and reload, Settings draws and scrolls. Full current Home/Recents lifecycle qualification remains open.','evidence/hardware-v35/v36-systemui-speed.json'),
'INPUT02':('PARTIAL','Software-window Settings draws correctly and completed actual scrolling. The normal GPU-window comparison reproduces missing labels and top-edge strips, despite primitive offscreen passes. Native GPU app rendering is not qualified.','evidence/hardware-v35/v36-settings-gpu.json'),
'NET02':('PASS','v36 native Android Wi-Fi off/on and automatic reconnect passed. netd and system_server retained their PIDs through ordinary-app DNS/TLS and a further20-second IDLETIMER observation window. Full electrical radio power-off is separate.','evidence/hardware-v35/v36-wifi-reconnect.json'),
'NET05':('PASS','BOOT42 kernel UID/packet-target/gateway-table fixes allow native DHCP, address assignment and default routing. Ordinary-app network report confirms the default route; no manual routes or firewall bypass.','evidence/hardware-v35/v36-wifi-reconnect.json'),
'NET06':('PASS','An ordinary app resolves two DNS addresses and completes HTTPS204 with TLS_CHACHA20_POLY1305_SHA256 over Wi-Fi after automatic reconnection. Android reports VALIDATED; both network/core processes remain stable.','evidence/hardware-v35/v36-wifi-reconnect.json'),
'NET07':('PARTIAL','The current install boot reconnects to the saved network, and off/on automatic reconnect plus Internet passes. Deep-sleep/suspend reconnect remains unqualified.','evidence/hardware-v35/v36-wifi-reconnect.json'),
'NET08':('PARTIAL','Native Wi-Fi now connects and supplies validated Internet. The airplane-mode/Wi-Fi override combination still needs its own qualification.','evidence/hardware-v35/v36-wifi-reconnect.json'),
'NET09':('BLOCKED','Client-mode Wi-Fi now works. Hotspot/AP capability, actual client connection and tethering still require separate driver/backend qualification; no hotspot credentials changed.','evidence/hardware-v35/v36-wifi-reconnect.json'),
'NET15':('PARTIAL','Native per-app uplink, DNS and TLS are now verified. VPN tunnel establishment, traffic and isolation remain unqualified.','evidence/hardware-v35/v36-wifi-reconnect.json'),
'APP16':('BLOCKED','A usable native uplink is now verified. Actual DownloadManager download/open behavior remains to be checked after current hardware/UI blockers.','evidence/hardware-v35/v36-wifi-reconnect.json'),
'GAPPS02':('PARTIAL','Google components are retained and ordinary-app Wi-Fi Internet now passes. Owner sign-in and a real Play Store download remain unqualified; no account actions taken.','evidence/hardware-v35/v36-wifi-reconnect.json'),
}
f=p/'FUNCTIONAL-CHECKLIST.md';text=f.read_text(encoding='utf-8');lines=text.splitlines()
for i,line in enumerate(lines):
 match=re.match(r'- \[[ x]\] \*\*([A-Z]+\d+) (.*?) - [A-Z_]+\*\*\.',line)
 if match and match[1] in updates:
  status,description,link=updates.pop(match[1]);lines[i]=f'- [{"x" if status=="PASS" else " "}] **{match[1]} {match[2]} - {status}**. {description} [evidence]({link})'
assert not updates,updates
text='\n'.join(lines)+'\n';counts=Counter(re.findall(r'^- \[[ x]\] \*\*[^\n]* - ([A-Z_]+)\*\*\.',text,re.M))
text=re.sub(r'^Counts: .*$', 'Counts: '+', '.join(f'{key}={value}' for key,value in sorted(counts.items()))+'.',text,flags=re.M)
text=text.replace('[Current hardware checkpoint](evidence/hardware-v35/final-status.json)','[Current hardware checkpoint](evidence/hardware-v35/v36-final-status.json)')
f.write_text(text,encoding='utf-8')
current='''# Current SM-T110 development state

Updated2026-11-11. System v36-GApps and BOOT42 are installed. This is an
engineering port with unfinished hardware integration and UI problems, not a
fully functional/public-release ROM. User authorizes verified fixes/build/flash
without repeated approval; physical accessory checks wait for the owner.

## Verified current result

- v36 fixes a real netd SIGSEGV: the old kernel emits IDLETIMER LABEL, while
  Android13 expected INTERFACE and passed null to ParseInt. Patch0099 accepts
  both and rejects missing/invalid labels. Eight actual ARM regressions pass.
- Native Wi-Fi off/on, automatic reconnect, ordinary-app DNS and HTTPS204 pass;
  Android reports VALIDATED. netd170 and system_server310 stayed alive through
  the test and an additional20-second timer window. No manual routing bypass.
- Native/Google components retained. Only netd changed in the v36 system image;
  reverse385024-byte delta retained. Both data profiles preserved, no physical
  SYSTEM/recovery write. Startup completed227.76s, SELinux Enforcing.
- Native SystemUI speed compilation succeeded (169500ms). Its reload plus warm
  startup allowed Settings to draw and scroll:80 presented frames over6.02s of
  scripted swipes including dispatch/settle time. This is NOT a smoothness pass,
  nor proof compilation alone caused the improvement.

## Remaining blockers and the next focused work

- Startup still has SystemUI/Google ANRs and heavy page/storage churn. A live
  snapshot showed mmcqd/loop I/O waits; vmstat had100448 major faults and23GB
  cumulative page input. These counters support investigating storage/memory
  pressure, not a declaration that eMMC is faulty. zram512MiB is enabled but
  unused, swappiness60. Do not blindly change memory policy.
- Compiled GPU primitive fixtures pass6 full600x1024 cases. Real native GPU
  Settings fails: backgrounds/vectors draw, text is absent and white strips
  corrupt the top. Captured hardware output proves ordinary-window correctness
  remains unresolved. Do not enable GPU app windows by default based on the
  primitive tests. Current debug.hwui.t110_window_gpu=false was restored.
  Candidate areas include glyph/texture/vertex handling, but none is established
  as the root cause yet. No additional boot was used for these comparisons.
- Wi-Fi live metrics still need work. wificond logs missing
  NL80211_STA_INFO_TX_FAILED and rejects the entire station report; its parser
  also only accepts32-bit rate attributes, while older kernels can use16-bit.
  Source identified, NO fix built yet. Keep unavailable counters distinct from
  fabricated zero failures; preserve the existing modern path and add tests.
- Bluetooth H4 transport source and SDIO identity match mbt8xxx; no module/HAL
  integration yet. Read BLUETOOTH-TRANSPORT-NOTES.md before loading anything;
  driver0666 policy must not enter production. Camera raw capture passed earlier,
  but Android provider, audio, sensors and capacitive-key LEDs remain unfinished.
- Native key mappings were owner-confirmed earlier. Physical accessories,
  pairing/audio, deep suspend, credential unlock and owner Google sign-in remain
  separate checks. Keep native Lineage/Google features; no removal to hide errors.

## Evidence and resume

Read evidence/hardware-v35/v36-final-status.json, v36-wifi-reconnect.json,
v36-systemui-speed.json, v36-settings-gpu.json and the updated FUNCTIONAL-CHECKLIST.
Framebuffer captures: hardware-tests/20261109-settings-wallpaper/v36-after-speed.png
(correct software Settings), v36-normal-gpu.png (failed GPU text/strips).
Detailed awake input/display/log snapshot: evidence/hardware-v35/v36-ui-diagnostics.
Older RESUME-LIVE-NETD.md and BOOT39/35 handoffs are historical; do not rerun their
installers. No build/test remains running after this checkpoint.

Never write physical SYSTEM/mmcblk0p15. Active system is a userdata loop image.
Current boot and recovery hashes, exact system hash and bootID are in the current
receipts. BOOT42 unchanged by v36. Reverse delta is retained on the tablet.

E SSD currently works; last Windows10-minute event checks showed no129/153 errors.
T110Build on E: /root/t110-build/lineage20 (full source/out-system).
Ubuntu on C: /root/t110-build/kernel-display-i2c (GCC4.6, out-gateway).
No active files moved to another drive. Keep current/rollback artifacts; do not
repeat earlier v32 deletion denials. No public binary/XDA release was made.
Existing community PRs remain recorded in community/contributions.json.
New isolated candidate0099 has real-device regression/reconnect evidence in
community/NETD-LEGACY-IDLETIMER.md; not pushed or submitted to Gerrit. Gerrit
account/agreement must be handled by owner; do not accept legal terms for them.
'''
(p/'CURRENT-STATUS.md').write_text(current,encoding='utf-8')
print(json.dumps(state,indent=2));print('CHECKLIST_COUNTS',dict(sorted(counts.items())))
