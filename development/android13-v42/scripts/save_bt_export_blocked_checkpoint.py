"""Save actual installed state; do not promote a compiled-but-unexported build."""
from pathlib import Path
from collections import Counter
import json,re
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';live=json.loads((e/'blocked-final-status.json').read_text())
assert live['system_revision']==38 and live['boot_revision']==45 and live['boot_server_netd_stable'] and live['wifi_dns_tls_pass'] and not live['pending_fixes_installed']
build=dict(status='NATIVE_COMPONENT_BUILD_REPORTED_SUCCESS_EXPORT_BLOCKED',native_build_exit_reported=0,
 target_modules=['com.android.btservices','t110_bt_init'],lookup_build_log=(e/'lookup-build-log.txt').read_text().strip(),
 watchdog_source=json.loads((e/'lookup-watchdog-source.json').read_text()),device_source=json.loads((e/'device-source.json').read_text()),
 binary_hashes_verified_after_export=False,rom39_built=False,rom39_flashed=False,
 clone_state='artifacts/lineage20-rom-v39-gapps/system.raw.incoming is a verified unmodified v38 clone; no new binaries applied',
 blocker='E path unavailable after disk153 at2026-11-11T23:45:45.7004369Z; export could not start')
(e/'combined-build-export-blocked.json').write_text(json.dumps(build,indent=2)+'\n',encoding='utf-8')
updates={
 'CORE01':('PARTIAL','v38/BOOT45 reaches Android boot_completed in236.16s. Current boot/core/netd identity remains stable and ordinary-app Wi-Fi DNS/HTTPS204 passes. UI responsiveness is not qualified.'),
 'NET10':('PARTIAL','The restricted driver and native HAL start automatically. Real controller identity and firmware callback work after a live identity-file mode correction. Native adapter startup still aborts on a stale lookup watchdog; the permanent fixes compiled but export is blocked by E disappearing.'),
 'NET11':('FAIL','Native adapter enable/discovery has not passed. Current Bluetooth is temporarily disabled to stop the failed initialization trial. Do not mark discovery, pairing or BLE traffic working from raw HCI command passes.'),
 'NET12':('BLOCKED','Requires the corrected native stack, then actual owner peer pairing/reconnect/bond persistence. No pairing performed.'),
 'NET13':('BLOCKED','Native Bluetooth audio provider is installed, but real audio is unported and no accessory audio test passed. SCO/offload requests are explicitly unsupported.'),
 'NET14':('BLOCKED','Raw controller features confirm LE capability. Real app scanning, BLE traffic, HID and file transfer remain unqualified while native adapter startup is blocked.'),
 'HW09':('PENDING_PHYSICAL','Normal vold configuration is installed for the actual external mmc1 slot. The current app inventory sees only mounted primary emulated storage; no removable card is present. No card was formatted. VFAT/FUSE available; exFAT unqualified.'),
}
f=p/'FUNCTIONAL-CHECKLIST.md';lines=f.read_text(encoding='utf-8').splitlines()
for i,line in enumerate(lines):
 m=re.match(r'- \[[ x]\] \*\*([A-Z]+\d+) (.*?) - [A-Z_]+\*\*\.',line)
 if m and m[1] in updates:
  status,description=updates.pop(m[1]);lines[i]=f'- [{"x" if status=="PASS" else " "}] **{m[1]} {m[2]} - {status}**. {description} [evidence](evidence/hardware-bt-sd/blocked-final-status.json)'
assert not updates
text='\n'.join(lines)+'\n';counts=Counter(re.findall(r'^- \[[ x]\] \*\*[^\n]* - ([A-Z_]+)\*\*\.',text,re.M))
text=re.sub(r'^Counts: .*$', 'Counts: '+', '.join(f'{key}={value}' for key,value in sorted(counts.items()))+'.',text,flags=re.M)
text=text.replace('[Current hardware checkpoint](evidence/hardware-v35/v36-final-status.json)','[Current hardware checkpoint](evidence/hardware-bt-sd/blocked-final-status.json)');f.write_text(text,encoding='utf-8')
(p/'CURRENT-STATUS.md').write_text('''# Current SM-T110 development state

Updated2026-11-12. Installed: v38-GApps / BOOT45. This remains an engineering
port with unfinished hardware and UI issues. Flash verified ready fixes without
repeated approval. Preserve native Lineage and Google functionality. No agents.

## Current verified state

- bootID bd64186a-aaa3-49b5-8406-1497456c536e, system_server317, netd170.
- System SHA4e7ca1a5e997bb1d08965c5cad2261f81c99eb6e32b4673dd63db419f9986e14.
- BOOT45 SHA2ca5248c7bc8bf814421cb6d4c6e7c060429a621b66141e5fd4afdbec4b905fa.
- SELinux Enforcing, normal GPU windows remain disabled. Core/netd/boot stable;
  ordinary-app Wi-Fi DNS/HTTPS204 still VALIDATED. No manual network bypass.
- Restricted mbt8xxx loads automatically, reads the real controller identity,
  and the native HAL runs with the built RUNPATH. Raw reset/version/features/
  address and four ARM H4 regressions pass. Native Bluetooth IS NOT working yet.
- Correct microSD vold slot rule is installed. No card currently present. The
  app sees primary emulated storage; its external app-directory list was empty.
  Investigate that before treating a later card probe as a complete storage pass.
- Both data profiles and TWRP retained; physical SYSTEM never written.

## Exact next blocker and prepared fixes

E disappeared after a disk153 read retry at2026-11-12 01:45:45 local. Both WSL
distros are stopped. SSD reconnect request is pending. The tablet remains on
the same v38 boot. Bluetooth was temporarily disabled to stop its failed trial.
No new boot, flash, physical SYSTEM write or recovery write is pending/running.

The two remaining startup fixes compiled successfully in the native build:

1. Init umask made controller_address0600; the HAL could not open it. Its live
   mode was corrected to0640 without changing content. The permanent loader
   now fchmods0640 before publishing the root:bluetooth file.
2. The lookup watchdog aborted after getService returned and firmware init
   completed. Patch0105 guards a completed lookup with shared atomic state.
   The500ms deadline and fatal missing-service behavior remain. The actual guard
   regression fails before/passes after, including1000 race trials. The callback
   uses Chromium's typed BindOnce argument; its native build now succeeds.

These compiled files are still on E. v39 is NOT exported, verified or installed.
The C v39 incoming file is only a verified unmodified v38 clone. Resume with
prepare_bt_v39.py after E access returns; it safely rechecks/reuses that clone.
Then run install_bt_v39.py automatically after checks. It updates only the loop
system image; BOOT45 is unchanged. Run qualify_bt_sd_v37.py, now pinned to v39,
only after that install. Do not run the PASS-only checkpoint updater prematurely.

## Remaining hardware and UI work

Real Bluetooth enable/discovery/BLE/pairing are unqualified. Audio, Android camera
provider/output, sensors, stock-working key LEDs and USB MTP remain unfinished.
Pairing, microSD, headphones/OTG, deep suspend and owner sign-in need physical
accessories/owner. Never format/adopt personal storage during detection checks.

Wi-Fi reconnect/DNS/TLS passed in v36 and current uplink passes in v38. Legacy
station metrics still need a separate fix. Do not invent zero unavailable stats.
GPU simple full-size fixtures passed but real Settings loses text/top strips;
keep debug.hwui.t110_window_gpu=false until actual native UI correctness passes.
Startup still takes about236s and UI lag/ANRs remain. SystemUI speed compilation
helped the previous software rendering path; it did not establish smoothness.

## Evidence and development locations

Read HARDWARE-BT-SD.md, FUNCTIONAL-CHECKLIST.md and evidence/hardware-bt-sd:
v38-installation.json, blocked-final-status.json, combined-build-export-blocked.json,
identity-mode-live-fix.json, lookup-watchdog-source.json and native failure logs.
No pairing/peer data is claimed tested; keep raw diagnostics private.

T110Build on E: /root/t110-build/lineage20 and /root/t110-build/out-system.
Ubuntu on C: /root/t110-build/kernel-display-i2c, GCC4.6/out-gateway.
Do not move active files between drives. Keep current/rollback images until
the new native checks pass; no cleanup of v37/v38 images has been performed.
Existing community PRs remain in community/contributions.json. No new public
ROM, XDA publication or Gerrit submission was made. Never rerun old installers.
''',encoding='utf-8')
(p/'RESUME-NEXT.md').write_text('''# Resume Bluetooth export after E reconnect

Read CURRENT-STATUS.md and evidence/hardware-bt-sd/combined-build-export-blocked.json.
Actual installed pair is v38-GApps/BOOT45; bootID bd64186a-aaa3-49b5-8406-1497456c536e.
The tablet stayed running; Bluetooth is temporarily disabled. Wi-Fi/core remain
stable. No build/test runs. No new flash should occur until image checks pass.

1. Verify E:/T110-build/WSL/ext4.vhdx is accessible and recent disk events. Start
   only T110Build. Verify its known identity, sources and successful lookup build
   log. Do not rerun the build unless evidence/outputs need rebuilding.
2. Windows: python SM-T110/scripts/prepare_bt_v39.py. It rechecks the existing
   unmodified v38 clone in the v39 incoming file, exports the newly compiled
   loader/JNI, preserves metadata and checks filesystem/delta/hash. Source hashes
   and the actual500ms watchdog regression are required. No v39 host receipt yet.
3. After it passes: python SM-T110/scripts/install_bt_v39.py. This one-shot is
   reviewed, identity/hash guarded, reversible, system-only; retains BOOT45/TWRP,
   both profiles and physical SYSTEM. No further approval needed.
4. Then python SM-T110/scripts/qualify_bt_sd_v37.py. Despite its historical name,
   it targets v39 and writes native-qualification-v39.json. It must prove fresh
   automatic0640 identity-file mode, native off/on, discovery/BLE requests,
   Wi-Fi TLS and process stability. Failed help exit was a test-harness issue;
   operational commands remain strict. No raw HCI probe while Android owns HCI.
5. Only after PASS update checkpoint/checklist to39/45. The prepared
   update_bt_sd_checkpoint.py still contains38 references and must be adjusted.
   Current partial checkpoint is accurate; never tick raw HCI as full Bluetooth.

All code patches0100–0105 and receipts are under SM-T110. Root init's platform
radio trigger is in work/core-boot/init.mrvl.rc; the vendor rc is now clean.
The canonical device source includes fchmod; the typed watchdog fix is in the
Bluetooth module source on E. Future build_bt_sd_rom.sh should also call
prepare_bt_lookup_watchdog.py before the full system build.

No microSD is present. Current storage probe sees mounted primary emulated
storage but no external app dirs. Card detection/mount/read-write still needs
real media; no formatting. Other hardware/UI blockers are in the checklist.

After v39 is truly qualified, remove superseded temporary full-image copies
only with hashes/reverse reconstruction verified. Keep current and real rollback
sources. Do not move clutter to D or repeat old v32 cleanup denials.
''',encoding='utf-8')
w=p/'BUILD-WORKSPACE.json';data=json.loads(w.read_text());data.update(state='v38-GApps / BOOT45 installed; Bluetooth native startup blocked; compiled v39 export waiting for E',phase='HARDWARE_FUNCTIONAL_REPAIRS_EXPORT_BLOCKED_E',
 installed_system_version=38,installed_boot_version=45,installed_system_sha256=live['system_sha256'],installed_boot_sha256=live['boot_sha256'],current_hardware_checkpoint='evidence/hardware-bt-sd/blocked-final-status.json',
 pending_system_artifact='artifacts/lineage20-rom-v39-gapps/system.raw.incoming',pending_system_sha256=None,pending_boot_artifact=None,pending_boot_sha256=None,pending_boot_status=None,
 full_build_blocker='Native build succeeded; E disappeared before component export',active_build_session=None,active_stage_session=None,active_test_session=None,development_paused=False,
 last_component_build_log=build['lookup_build_log'],output='T110Build:/root/t110-build/out-system')
w.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');print('ACTUAL_V38_STATE_AND_BLOCKED_V39_RESUME_SAVED_NO_FALSE_PASS')
