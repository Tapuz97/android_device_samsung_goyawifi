"""Record confirmed failures without falsely promoting a compiled artifact to PASS."""
from pathlib import Path
import json,re
p=Path(__file__).resolve().parents[1]
assert not (p/'evidence/ui-system-hang-20261112/v40-installation.json').exists(),'Historical v39 checkpoint; do not overwrite a later installation'
install=json.loads((p/'evidence/hardware-bt-sd/v39-installation.json').read_text())
assert install['boot_id']=='96631e42-d8b9-491d-b471-085eafbc91cf'
(p/'CURRENT-STATUS.md').write_text('''# Current SM-T110 development state

Updated 2026-11-12. Installed **v39-GApps / BOOT45**. Unfinished engineering
port: owner-confirmed UI freezes and actual ANRs remain. No verified UI fix.

## Current identity and safeguards

- BootID96631e42-d8b9-491d-b471-085eafbc91cf, system_server320 through captured
  failures. Boot completed229.9s. SELinux Enforcing.
- System SHA f7d1cbd95656ec085e504b0931e1b92cc9a19b0d0bea944cb178899cbfccf2b9.
- BOOT45 SHA 2ca5248c7bc8bf814421cb6d4c6e7c060429a621b66141e5fd4afdbec4b905fa.
- Only userdata loop system was updated. NEVER write physical SYSTEM p15.
  Both profiles and TWRP retained. Keep v38 rollback and verified reverse delta.
- Installation receipt: evidence/hardware-bt-sd/v39-installation.json.
- debug.hwui.t110_window_gpu=false: native GPU app windows still lose text/strips.
  JIT remains off because old kernel lacks ART's required dual-view mappings.

## Priority: actual UI/system unresponsive dialogs

Owner confirmed freezes then "process system isn't responding." Actual logs are
in evidence/ui-system-hang-20261112. NotificationShade input/focus waited5002ms;
launcher and Google Search broadcast ANRs also occurred. Idle no-ANR snapshots
were not a fix. SystemUI/launcher are AOT speed compiled already.

Captured load:89-98% CPU busy,19-23% I/O wait, mmcqd/loop/kswapd activity and many
major faults. Search remains extract-only; updated GMS verify-only with JIT off.
This supports contention, not an exclusive proven root cause. A WMS lock-owner
snapshot during SIGQUIT may be an ART suspension artifact, not proven deadlock.

On-device Search compilation failed after573.7s at ART's570000ms watchdog.
The same route failed historically in offline-v41/gapps-v31-test. No GMS compile
followed. Do not repeat blindly, remove Google features, hide ANRs or raise
production timeouts. No baseline profile/ProfileInstaller receiver is supplied.

PC-side normal ART preoptimization is being prepared: exact unchanged private
APK, matching installed boot images and optional-library hashes, enforced uses
libraries. scripts/build_private_search_preopt.py produces only OAT/VDEX, not an
installed ROM. Inspect evidence/ui-system-hang-20261112/private-search-preopt
manifest/log and running process before resuming. Host success is not UI PASS.
No reboot occurred after this ANR capture; normal Bluetooth disable stopped its
failing trial. Preserve native Lineage and Google functionality.

## Hardware status

v39 was rebuilt/exported/verified/installed after E reconnect. Its fresh identity
file0640 and runtime loader/JNI hashes pass. The watchdog completion guard is
actually loaded, yet native Bluetooth still fails the500ms getService watchdog.
Do not call it a fixed stale watchdog: native-qualification-v39.json is FAIL.
Raw controller/H4 passes do not prove discovery, pairing, BLE or audio.

MicroSD rule installed; no physical card present. Real camera provider, audio,
sensors, stock-working key LEDs and MTP remain unfinished. Physical navigation
had owner passes. See FUNCTIONAL-CHECKLIST.md for separate gates.

## Build/storage and authorization

E holds T110Build full source/output; Ubuntu on C holds kernel/tools. Earlier
E read retry damaged an old build log tail. This turn forced both components to
rebuild after source-hash verification and exported small verified payloads to C
before packaging in Ubuntu. Do not trust the damaged earlier success log.
No evidence establishes storage permanently fixed. No public push/release made.

Verified build/flash is authorized without repeated permission. No subagents.
Preserve active/rollback files in place; delete obsolete outputs, never move
clutter to D. Tablet is unchanged since the ANR capture, apart from the failed
normal ART optimization attempt. Always verify current identity before writes.
''',encoding='utf-8')
(p/'RESUME-NEXT.md').write_text('''# Resume the actual UI ANR investigation

Read CURRENT-STATUS.md. Installed v39-GApps/BOOT45; actual UI and system dialogs
are confirmed. Do not rerun old v39 installer or PASS-only Bluetooth updater.

1. Check active host compiler and private-search-preopt manifest/log under
   evidence/ui-system-hang-20261112. scripts/build_private_search_preopt.py uses
   the existing host ART pipeline, exact installed private APK, matching boot
   images/libraries, strict uses-library checks. It installs nothing.
2. If successful, validate ARM/compiler filter/dex locations/classloader context.
   Integrate only OAT/VDEX into a verified v39 clone if it fits. Preserve metadata
   and SELinux labels, check filesystem/content/hash and reversible delta.
3. Flash verified candidate automatically, retaining BOOT45/TWRP, physical SYSTEM
   and both data profiles. Only write the unmounted userdata system loop file.
4. Verify ART accepts code, then actual shade/Settings interaction, new ANRs and
   CPU/I/O/fault measurements. Idle boot or compiled file alone is not UI PASS.

Do not retry on-device Search speed compilation: it failed570000ms watchdog now
and historically. No supplied baseline profile; GMS compile never started. Do
not disable/remove Google apps or enable the visually broken GPU window path.

Native Bluetooth remains FAIL at500ms service lookup with the new guard loaded.
It was normally disabled to stop failed trials. MicroSD needs physical media.
No other boot occurred after capture. Preserve v38 rollback until stability.

Canonical device: work/device/samsung/t110_bringup. Full source/output in
T110Build:/root/t110-build/lineage20 and out-system. E had read retries: verify
sources/artifacts and export small results to C before distro exits. No agents.
''',encoding='utf-8')
f=p/'BUILD-WORKSPACE.json';state=json.loads(f.read_text())
state.update(state='v39-GApps / BOOT45 installed; native Bluetooth qualification FAIL; owner-confirmed UI/system ANRs under investigation',
             current_installed_system_sha256=install['system_sha256'],current_installed_boot_sha256=install['boot_sha256'],
             current_installed_boot_id=install['boot_id'],current_ui_evidence='evidence/ui-system-hang-20261112',ui_fixed=False)
f.write_text(json.dumps(state,indent=2)+'\n')
f=p/'FUNCTIONAL-CHECKLIST.md';s=f.read_text()
replacements={
 'CORE01':'**CORE01 Boot reaches Android and launcher - PARTIAL**. v39/BOOT45 boot_completed229.9s, but owner confirms UI/system freezes. [evidence](evidence/hardware-bt-sd/v39-installation.json), [ANRs](evidence/ui-system-hang-20261112/capture.json)',
 'CORE02':'**CORE02 Startup completes without service ANRs or automatic restarts - FAIL**. Owner-confirmed UI/system dialogs, NotificationShade5002ms input/focus timeout and launcher/Search broadcast ANRs in current v39. Netd fix does not solve these. [evidence](evidence/ui-system-hang-20261112/capture.json)',
 'NET10':'**NET10 Bluetooth adapter/driver/HAL available - PARTIAL**. v39 fresh identity0640 and exact runtime loader/JNI pass. Native lookup still hits500ms watchdog with the new guard loaded; no full adapter pass. [evidence](evidence/hardware-bt-sd/native-qualification-v39.json)',
 'NET11':'**NET11 Bluetooth enable/disable and discovery - FAIL**. v39 native qualification failed. Bluetooth normally disabled to stop repeated failed startup. Raw HCI success does not prove discovery/pairing/BLE. [evidence](evidence/hardware-bt-sd/native-qualification-v39.json)'}
for key,value in replacements.items():
    s,n=re.subn(r'^- \[ \] \*\*'+key+r' .*$', '- [ ] '+value,s,flags=re.M);assert n==1,(key,n)
s=s.replace('[Current hardware checkpoint](evidence/hardware-bt-sd/blocked-final-status.json).','[Current installation](evidence/hardware-bt-sd/v39-installation.json). [Native Bluetooth failure](evidence/hardware-bt-sd/native-qualification-v39.json).')
f.write_text(s,encoding='utf-8')
print('Current v39 installation, failed Bluetooth and actual UI ANRs recorded; no new PASS claims')
