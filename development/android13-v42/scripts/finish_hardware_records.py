"""Reconcile source-only changes and the final installed state, without device IO."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35'
for name in ('build_netd_targets_kernel.sh','build_gles_audit.sh'):
    f=p/'scripts'/name;f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
candidate=(e/'netd-targets.config').read_bytes();metadata=json.loads((e/'netd-targets-source.json').read_text())
assert b'\r' not in candidate and hashlib.sha256(candidate).hexdigest()==metadata['candidate_config_sha256']
status=json.loads((e/'final-status.json').read_text())
assert status['temporary_test_app_removed'] and all(v=='null' for v in status['gpu_settings'].values())
summary='''# Current hardware checkpoint - supersedes earlier active notes

Read ../../CURRENT-STATUS.md and ../../RESUME-NEXT.md first. Installed v34 system /
BOOT39, SHA33462a6a2cffc1695ac8d8f986d42eac13b12b0708a5eb9db26f66c9baa73701,
boot a1d15767-b169-4593-818b-63132704d969, system_server311, Enforcing. Boot completed
in227.89s. final-status.json records the closing ordinary-app network failure.
Temporary QA APK and verified boot-transfer file removed, all4GPU settings null,
stay-on0, Advanced Restart1. No private publication or cleanup-denial retries.

User wants hardware first, then software. Preserve all native Lineage/Google apps.
Do not ask again before flashing a verified ready fix. No agents permitted.

0095 UID routing is applied/built/installed: all71 virtual-kernel checks PASS;
Android's real UID rules are now accepted. The old parsing discrepancy is RESOLVED:
rtnetlink_rcv_msg's OUTER attribute loop rejects attrs above rta_max, before
fib_rules/nla_parse. Modern FRA_UID_RANGE20/RTA_UID25, socket/flow UID and IPv4 cache
identity are implemented. USER_NS is disabled. Source/baseline/candidate live in
Ubuntu:/root/t110-build/kernel-display-i2c and uid-routing-backport/{base,candidate}.
Do not regenerate from unknown edits: source/apply helpers now check known hashes.
Old output out-display-i2c remains; new out-uid-routing zImage SHA
b32abb8d3bc55f9e13fed05abb58ed3d6a075581eacbf0111918d187aba42121.

Actual installed stripped mlan/sd8xxx and old galcore runtime sections/normalized
relocations match new modules. Differences ignored are debug, build-id, srcversion
and intree metadata only; vermagic/dependencies/parameters remain checked. This
allowed BOOT39 with byte-identical old ramdisk and NO2GB system rebuild/transfer.
BOOT38 rollback remains SHA b5bab81d2693d3b8b3e479963275173c938b3110e3110fa20489f72cae5694c5.
Never write physicalSYSTEMp15 or rerun the recorded BOOT39 installer.

Next Wi-Fi blocker: native networkAddInterface RemoteIO121; route additions then
ENODEV19 because interface was not committed. Running config disables XT_MARK,
XT_CONNMARK and XT_TARGET_IDLETIMER, though code is present. Authentication/DHCP
work; normal app DNS/HTTPS does NOT. 0096 defconfig patch and netd-targets.config
are staged only, NOT BUILT/APPLIED. build_netd_targets_kernel.sh prepares
out-netd-targets from exact candidate config/source95. After recovery of Linux,
build and probe real xtables revisions with netd_target_probe.c (10 checks; this
new C source is NOT COMPILED). Run a meaningful virtual check, compare installed
module runtime ABI again, package a NEW boot revision and test native Internet.
Do not strip UID attributes, leave manual routes, enable a duplicate OWNER match
(QTAGUID is already enabled), or claim Internet from root gateway ping.

Graphics evidence:
- raw-gpu.json: actual GLES2 shader/client arrays/VBO upload/orphan-subdata pass,
  both glReadPixels and queued ImageReader pixels correct.
- raw-gpu-skia-state.json: same fragment shader semantics/blending/32768-byte VBO/
  double orphan-subdata also pass all3 modes. Total6raw cases, both readback paths.
- hwui-uniforms.json/hwui-state.json: HWUI still4096red/0green; compile/link good,
  uniform .03125,-1,-.03125,1, attribposition0/color1; blendONE/ONE_MINUS_SRC_ALPHA,
  FUNC_ADD. Post-swap callback context valid, glFinish0, framebuffer and queued
  image stillred. Post-swap finish DOES NOT exclude a pre-swap resolve/order bug.
- Exact call order still differs: Skia uploads before framebuffer clear/program
  creation; raw replay uploads afterwards. Need actual Skia payload/pre-swap data.
- New gles_audit.c logs first48VBO bytes and performs tiny64x64 pre-swap readback.
  This source is NOT COMPILED. Existing .so/APK are older and not valid evidence
  for those hooks. Run build_gles_audit.sh first; it now emits gles-audit-build.json.
  APK builder --gles-layer requires matching source and library hashes.
- Reinstall temporary helper, then one new labeled HWUI trace. Green pre-swap but
  red queued points toward KHR presentation; red pre-swap means inspect vertex/
  color data and preparation order. No global production HWUI enable yet.
- Old gpu_readback_probe.cpp only did scissor/clears, not shader geometry.
- QA debuggable mode caused10s attach timeout; use metadata
  com.android.graphics.injectLayers.enable=true instead. Nondebuggable launches
  work. Native Lineage apps were not modified to fix this test-fixture issue.

Bluetooth read-only inventory: three SDIO functions, no loaded mbt8xxx, no HCI/
BluetoothManager/HAL. Matching module exists in out-uid-routing. Button sysfs
sec_touchkey lacks brightness. Optional RT5033 V_TOUCHKEY_2V2 source rail is absent
from actual PM800 runtime regulator inventory: do not toggle guessed supplies.
Owner confirms fitted LEDs work on stock. Camera raw640x480USERPTR is earlierPASS;
native provider/output remains. Audio88PM805/sensors still incomplete.

BLOCKING HOST STATE: external E logged fresh Disk153 read retries; native WSL
requests and Windows PowerShell stalled. Bounded wevtutil evidence in
host-storage-latest.txt. Exact task-owned stale wrappers were cancelled via native
Windows APIs; no unrelated processes/services reset. wsl--shutdown exec54097
completed0. Subsequent Ubuntu-only machine-id/startup exec63889 still hangs; no
build is active. User reconnect request is pending. Cancel/await any obsolete
startup requests before new builds; do not leave a queued shutdown to stop them.
Ubuntu registry BasePath is C:\\Users\\Gal\\AppData\\Local\\Packages\\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\\LocalState,
machineid3fa9d65f37d2414bb2f2b18f86ca1736. T110Build E:\\T110-build\\WSL, machineid
cd27023803954a89ad7c30407399c847. Device names sdd/sde change, verify contents/IDs.
Use tools.exec_command shellcmd.exe/loginfalse while PowerShell is stalled. For
quoted/compound host commands use Python argument arrays; cmd quoting through this
tool did not preserve python-c quoted strings. Never delete/re-register a distro
to bypass a bad drive. Wait for the owner to reconnect E, then resume the prepared
network build and native trace. Do not repeat the old diagnostics/whole ROM export.
'''
(e/'RESUME-ACTIVE.md').write_text(summary,encoding='utf-8')
(p/'evidence/functional-followup-20261111/ROUTING-BLOCKER.md').write_text('''# Superseded routing blocker - see hardware-v35

The previous UID-attribute EINVAL is fixed by0095 and installed BOOT39. Its exact
source was the OUTER rtnetlink_rcv_msg attribute validation against FRA_MAX17,
before nla_parse. It is no longer an unresolved source/runtime discrepancy.

All71 isolated real-kernel regressions pass, actual Android UID rules are accepted.
Wi-Fi auth/DHCP work. Native networkAddInterface now fails RemoteIO121 with missing
packet-marking support; real routes/ordinary-app Internet remain blocked. The
running config disables MARK/CONNMARK/IDLETIMER;0096/candidate config are staged but
not built. See ../hardware-v35/RESUME-ACTIVE.md and ../../CURRENT-STATUS.md.

Old traces remain valid historical evidence for the preceding failure. Do not
repeat old UID-isolation probes or omit UID selectors as a workaround.
''',encoding='utf-8')
(p/'evidence/functional-followup-20261111/GRAPHICS-BLOCKER.md').write_text('''# HWUI blocker - latest evidence in hardware-v35

The original HWUI64x64 probe remains a pixel failure:4096red,0green. New direct
GLES2 shader tests pass(client arrays, VBO upload, orphan/subdata), with correct
GPU and queued CPU readback. Replaying shader/blend/32768-byte buffer also passes.
HWUI uniforms, bindings and blend are correct; post-swap finish/readback staysred.

Next: compile the prepared native payload/pre-swap readback trace after Linux
recovers. Do not treat its current source as compiled. Inspect actual vertices,
preparation order and KHR presentation before enabling production HWUI. Existing
production software-window fallback is unchanged. The historical explicit
gpu_readback_probe.cpp tested clears/scissor, NOT shader geometry; use the new
raw-gpu*.json instead. See ../hardware-v35/RESUME-ACTIVE.md.
''',encoding='utf-8')
print('Installed state, source-only fixes, graphics findings and host blocker recorded')
