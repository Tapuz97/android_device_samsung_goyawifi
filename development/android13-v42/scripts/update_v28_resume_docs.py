"""Refresh resume entry points from the recorded v28 outcome, retaining history."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
current='''# Current state, 2026-11-10 — installed v28 / BOOT v31

Read evidence/offline-v41/result.json, startup-findings.md and README.md first.
The full build and verification succeeded on E after moving the SSD to another
laptop USB port. E is usable; the earlier E timeout checkpoint is historical.

System v28 and matched BOOT v31 were installed through TWRP, preserving data,
unchanged recovery and the verified v27/v29 rollback. No writes to SYSTEM.
One requested full boot reached Android, user0 unlocked, system_server309,
boot c1f5a9b6-375a-44b8-9a7f-a18065029891. This is not a fully working ROM.

Three installed normal screencap PNGs match the real framebuffer exactly;
native Android brightness40/220 drives panel40/220. Temporary screen settings
were restored. ADB seqpacket socket and final Java classpaths are installed.
Startup still has SystemUI/fused-location ANRs, initial ueventd SIGSEGV/respawn,
46.815s real-entropy wait and severe memory pressure with zram unconfigured.
Animation exit225.451s; do not claim boot speed fixed. Timezone persists but
RTC/wall-clock persistence failed (about42.8minutes behind host after reboot).

USB disappeared during the first normal-app H264 decoder initialization.
No result was retrieved; neither successful decode nor a kernel panic is proven.
Windows sees no Samsung device; a3-minute read-only watch did not recover ADB.
Owner screen/button observation is pending. No further reboot/flash was requested.
On reconnection preserve last_kmsg/current dmesg/QA report/ANR traces before
changing anything. QA app remains installed; cleanup is pending reconnection.
Use scripts/watch_v28_disconnect.py for read-only collection; if recovery opens,
adapt paths to its outer userdata mount. Keep on-device rollback intact.

FUNCTIONAL-CHECKLIST.md now records42PASS,15FAIL,19PARTIAL,27BLOCKED and
11PENDING_PHYSICAL, plus8 other/deferred items. Immutable baseline unchanged.
Camera, Wi-Fi/Bluetooth, sensors/GNSS, real audio and accessory checks remain open.
Owner is home/nearby and has the accessories. Do not redo the whole baseline.
Build/flash authorization persists; no repeated permission/readiness prompts.

FEATURE-BACKLOG.md records genuine DT2W feasibility investigation and native
Recents Clear all with an icon before text. Trebuchet already implements the
action; do not add a duplicate. Functional fixes remain the priority before the
UI/performance/features/HQ wallpaper phase. Preserve all native Lineage features.

## Historical v27 integration details (not the current installed pair)
'''
path=p/'CURRENT-STATUS.md';old=path.read_text(encoding='utf-8');marker='## Previous v27 integration details';assert marker in old
path.write_text(current+old.split(marker,1)[1],encoding='utf-8')
resume='''# Resume next, 2026-11-10

Current installed pair is system v28 / BOOT v31, not v27/v29. Read the latest
CURRENT-STATUS.md and evidence/offline-v41/{result.json,startup-findings.md,README.md}.
Full build access on E was restored by changing laptop USB port. Both final
system builds succeeded; do not duplicate the checkout on C or treat E as blocked.

One combined boot reached Android; capture pixel lifetime fix and native lights
integration passed. Startup remains failed (SystemUI/fused-location ANRs,
225.451s animation, early entropy wait, pressure with zram disabled, ueventd
crash/respawn). RTC persistence also failed. Hardware kernel includes ION_MAP,
but the codec check lost USB at first H264 decode and no result was retrieved.

Current physical tablet state is unknown: Windows has no Samsung USB device.
Owner was asked what is on screen and whether any buttons were pressed; answer
is pending. Three-minute read-only watch expired. No further reboot was requested.
First retrieve last_kmsg/dmesg and the saved QA report/ANRs when USB returns.
QA app needs removal after its report is saved. Screen preferences were restored.
Preserve existing TWRP, v27/v29 host and on-device rollback, and the new v28/v31
pair. Do not mix old bootstrap policy with the new system or write raw SYSTEM.

Functional checklist updated; immutable baseline preserved. Do not redo all122
checks or start a new test before understanding the interrupted decoder test.
The owner remains nearby for required physical steps; automatic build/install
authorization persists. Native DT2W feasibility and Recents Clear all/icon
requests are in FEATURE-BACKLOG.md for the later feature phase.

## Earlier v27 context (historical)
'''
path=p/'RESUME-NEXT.md';old=path.read_text(encoding='utf-8');marker='## Earlier v27 context';assert marker in old
path.write_text(resume+old.split(marker,1)[1],encoding='utf-8')
print('Current status and resume entries updated; historical evidence retained')
