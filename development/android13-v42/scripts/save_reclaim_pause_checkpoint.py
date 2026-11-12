"""Save the owner's pause state; do not reboot, test, build or flash anything."""
from pathlib import Path
import datetime,json,os,re,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112'
install=json.loads((e/'v41-installation.json').read_text());assert install['status']=='ANDROID_BOOT_COMPLETED_ART_ACCEPTANCE_AND_UI_RETEST_PENDING'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
r=subprocess.run(adb+['shell','cat /proc/sys/kernel/random/boot_id; pidof system_server com.android.systemui; cat /proc/sys/vm/swappiness; getprop init.svc.t110-logcat; getenforce'],capture_output=True,timeout=20)
assert r.returncode==0
current=r.stdout.decode(errors='replace').replace('\r','').strip();assert current.splitlines()[0]==install['boot_id']
feedback=dict(time=datetime.datetime.now().astimezone().isoformat(),owner_report='it is better but still not perfect. good for now',
              development_paused=True,physical_responsiveness='IMPROVED_NOT_FULLY_FIXED',ui_fixed=False,current_read_only_snapshot=current,
              dev_snapshot_worker_stopped=True,dev_file_logcat_stopped=True,no_host_scrcpy_or_adb_logcat_monitor_found=True,
              live_swappiness=100,live_changes_persist_across_reboot=False,
              pending_source_changes=['opt-in periodic boot snapshots','exact init swappiness SELinux node/type'],
              policy_build_status='FAILED_EXISTING_PUBLIC_API_FREEZE_CHECK_NOT_EXPORTED_OR_INSTALLED')
(e/'owner-pause-checkpoint.json').write_text(json.dumps(feedback,indent=2)+'\n')
(p/'CURRENT-STATUS.md').write_text('''# Current SM-T110 development state

Updated2026-11-12. **Paused at the owner's request: better, not perfect; good for
now.** Leave the tablet on its current v41-GApps/BOOT47 boot. No active test,
flash or build remains. Do not resume until asked.

## Installed pair and protection

- BootID51a85a32-e3ae-4229-b385-aea561461877; system_server317.
- System SHA a4e11ac1a749ae31f43118d1a0080a0dff7290ed30e2a3b0583467e4a03e114f.
- BOOT47 SHA 553f292654a703cb259c3e77bd77370e1c6b968f13e86ce886b3d4caa8e2b085.
- Android boot_completed234.63s, SELinux Enforcing. UI is not fully fixed.
- Read-only system loop file on userdata; NEVER write physical SYSTEM p15.
  Both Android data profiles and TWRP retained. Normal GPU app windows remain
  disabled; JIT remains disabled. Do not casually enable either.
- Immediate rollback is v40/BOOT46, with host images retained and the complete
  forward/reverse set plus both boot images in Android
  /stage-data/local/tmp/t110-v41-reclaim-paths-delta
  (TWRP: /data/local/tmp/t110-v41-reclaim-paths-delta).
- Obsolete v40 transfer files411639808bytes were actually deleted, not moved.
  The new immediate rollback remains. Redundant extracted C APK230477392bytes
  was deleted; the pinned MindTheGapps original archive remains.

## Verified improvements and limits

BOOT47 disables only Samsung ZRAM_FOR_ANDROID/RTCC2, retaining standard swap and
ZRAM. Those legacy options forced may_swap=0 in normal reclaim. Existing512MiB
swap had been completely unused despite severe file-cache thrashing. Corrected
MM passed an actual ARM pressure/swap/data-integrity test; all four installed
graphics/radio module interfaces and allocated code/relocations matched.
Actual tablet swap-out/in now occurs. See KERNEL-RECLAIM.md and evidence.

The unchanged private Google Search APK is host-precompiled with ART's space
filter and the actual runtime shared-library paths. It is selected as prebuilt
and actual executable Velvet.odex mappings were verified. Full speed code was
too large for the signed32-bit bootstrap image geometry. Space mode leaves large
methods interpreted. No APK/Lineage/Google feature was removed.

The combined full-boot interaction test STILL FAILED with a5004ms Notification-
Shade input ANR and a Search service ANR. A same-boot swappiness100 trial also
had a new SystemUI SCREEN_OFF ANR. Do not report the UI as repaired or smooth.
Before/after event sets distinguish old baseline records; the fused-location
event was already in baseline and is not established as a fresh startup failure.

## Current live settings: not yet persistent

The intended init swappiness100 write was proven denied: node has generic proc
label. Current boot was set to100 through the engineering ADB shell with SELinux
still Enforcing. After that, swap reached30764KiB used during the measured trial.

Our diagnostic snapshot worker was continuously flushing full kernel buffers
every2s for660samples. Its exact executable/FDs were checked, and only that worker
was terminated. Saved logs and init/system_server were retained. The separate
verbose t110-logcat file-writing service was also stopped through init. No host
scrcpy or adb-logcat monitor was found. Owner then reported improvement, not a
complete fix. These changes apply to THIS boot: BOOT47 restarts development
logging and returns to the blocked swappiness write after reboot.

## Pending source, deliberately not installed after pause

work/core-boot/stage.c now makes periodic snapshots opt-in with a root-owned,
non-writable regular marker in t110-bootlogs/periodic-enabled. Default preserves
one early snapshot and boot checkpoints. This new bootstrap has NOT been built
or boot-tested. Existing BOOT47 remains unchanged.

Canonical device genfs_contexts/t110_bootlog.te add only proc_t110_swappiness for
/sys/vm/swappiness and init rw_file_perms. The two source files were synced to E.
The normal selinux_policy build FAILED its existing public API freeze test:
public/attributes and public/domain.te differ from prebuilts/api/33.0. No new
policy was exported or installed. Do not disable the freeze/neverallow checks
or overwrite API snapshots blindly. Audit the pre-existing public modifications
before rebuilding this exact vendor-node fix. No compiler remains running.

## Other functionality

Native Bluetooth remains previously failed/unqualified; no new radio trial this
turn. MicroSD needs real media. Camera provider, audio, sensors, key LEDs and MTP
remain unfinished. Radio code was preserved, not newly functionally qualified.
Keep the functional checklist honest. No public push, Gerrit or release this turn.
''' ,encoding='utf-8')
(p/'RESUME-NEXT.md').write_text('''# Resume only when the owner asks

Owner paused: tablet improved after stopping development snapshot/file writers,
still not perfect. Leave current boot alone. Read CURRENT-STATUS.md and
evidence/ui-system-hang-20261112/owner-pause-checkpoint.json.

Installed v41-GApps/BOOT47. Actual executable Search preopt and normal compressed
swap now work, but automated interaction STILL produced SystemUI ANRs. Live
swappiness100 and stopped debug writers are not persistent across reboot.

Next authorized development pass:

1. Review/compile/test the already-prepared opt-in snapshot change in stage.c.
   Also make t110-logcat diagnostic opt-in: currently init.mrvl.rc starts it on
   early-init. Preserve normal Android logd; do not remove platform logging.
2. Audit the EXISTING platform public policy/API freeze differences. The new
   exact-node init permission is in canonical device source and E, but the build
   failed public/attributes/domain.te vs API33. Do not skip tests or blindly copy
   snapshots. build_reclaim_policy.sh is one-shot: source-copy assertions will
   reject rerun after it already copied files. Verify reclaim-policy-source.json
   and continue only the build phase once the actual freeze issue is resolved.
3. Export validated small policy outputs to C BEFORE E distro exits. A new system
   policy and identical embedded bootstrap policy must be packaged together;
   retain BOOT47 kernel and hardware modules. No candidate48/42 is built yet.
4. Build/verify a combined persistent logging/permission update before another
   full boot. Standing automatic verified flash authorization remains; the user
   paused current development, so do not act on that until they resume.
5. Continue actual UI responsiveness/JIT/native GPU investigation after that.
   No generic timeout inflation, removing Google/Lineage features or false PASS
   from idle boots. Native GPU windows and JIT remain disabled until supported.

Useful evidence: v41-installation.json, v41-boot47-ui/result.json,
v41-live-policy-ui/result.json, v41-live-swappiness.json,
v41-boot-logger-stopped.json, dev-monitor-stopped.txt,
v40-transfer-pruned.json, qemu-standard-reclaim.json,
kernel-standard-reclaim.json and reclaim-policy-build.log.

Immediate complete rollback: v40 system / BOOT46, host full images plus device
v41 forward/reverse delta and both boots. Never write physical SYSTEM p15.
Both profiles retained. E worked during this pass; historical read retries remain
a concern, no new disk129/153 events in the final8-minute check. No agents.
''' ,encoding='utf-8')
f=p/'BUILD-WORKSPACE.json';state=json.loads(f.read_text());state.update(state='PAUSED_BY_OWNER: v41-GApps / BOOT47 installed; owner reports improved but not perfect after live policy and stopped debug writers',
 current_installed_system_sha256=install['system_sha256'],current_installed_boot_sha256=install['boot_sha256'],current_installed_boot_id=install['boot_id'],
 ui_fixed=False,active_operation=None,pending_policy_build='FAILED_PUBLIC_API_FREEZE_CHECK_NOT_EXPORTED',kernel_output='Ubuntu:/root/t110-build/out-standard-reclaim')
f.write_text(json.dumps(state,indent=2)+'\n')
f=p/'FUNCTIONAL-CHECKLIST.md';text=f.read_text(encoding='utf-8')
changes={
 'CORE01':'**CORE01 Boot reaches Android and launcher - PARTIAL**. v41/BOOT47 boot_completed234.63s, Enforcing. Owner reports improvement after live swap policy and stopped diagnostic writers, still not perfect. [evidence](evidence/ui-system-hang-20261112/owner-pause-checkpoint.json)',
 'CORE02':'**CORE02 Startup completes without service ANRs or automatic restarts - FAIL**. Current v41/BOOT47 full-boot interaction produced NotificationShade5004ms input and Search service ANRs. A later live policy trial had a SystemUI SCREEN_OFF ANR. Owner improvement after stopping debug snapshot writer is not a complete fix. [evidence](evidence/ui-system-hang-20261112/v41-boot47-ui/result.json)',
 'CORE08':'**CORE08 Application lifecycle, Home and task switching - PARTIAL**. Current Settings/shade/Home commands run, but SystemUI ANRs/restarts remain in automation. Owner reports better, not perfect after diagnostic writer stop. [evidence](evidence/ui-system-hang-20261112/owner-pause-checkpoint.json)'}
for key,value in changes.items():
 text,count=re.subn(r'^- \[ \] \*\*'+key+r' .*$', '- [ ] '+value,text,flags=re.M);assert count==1
f.write_text(text,encoding='utf-8')
print('Paused state saved; tablet unchanged; no additional test, build or flash')
