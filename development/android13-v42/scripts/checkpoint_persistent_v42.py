"""Record the verified installed defaults without claiming an overall UI fix."""
from pathlib import Path
import json,re
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112'
install=json.loads((e/'v42-installation.json').read_text());result=json.loads((e/'v42-persistence/result.json').read_text())
assert result['status']=='PASS_PERSISTENT_LOGGING_AND_MEMORY_DEFAULTS' and not result['live_overrides_applied']
assert install['boot_id']==result['boot_id'] and all(item['pass_'] for item in result['checks'].values())
system=json.loads((p/'artifacts/lineage20-rom-v42-gapps/host-verification.json').read_text())
boot=json.loads((p/'artifacts/android13-boot-v48/provenance.json').read_text())
assert boot['paired_system_sha256']==system['sha256']==install['system_sha256']
assert system['paired_boot_sha256']==boot['full_boot_sha256']==install['boot_sha256']
boot.update(status='INSTALLED_FRESH_BOOT_DEFAULTS_VERIFIED',hardware_validated=True,hardware_validated_scope='Boot, unchanged kernel, logging defaults and init memory control; not complete UI/hardware qualification')
(p/'artifacts/android13-boot-v48/provenance.json').write_text(json.dumps(boot,indent=2)+'\n')
summary=dict(status='INSTALLED_PERSISTENCE_VERIFIED',installed_pair='v42-GApps / BOOT48',boot_id=install['boot_id'],
             system_sha256=install['system_sha256'],boot_sha256=install['boot_sha256'],bootstrap_policy_sha256=boot['bootstrap_policy_sha256'],
             checks=result['checks'],live_overrides_applied=False,ui_fully_fixed=False,
             native_policy_build='PASS_ALL_85_ACTIONS',policy_export='PASS_AFTER_CORRECTING_EXPORT_TOOL_INVOCATION',
             rollback='v41-GApps / BOOT47; complete forward/reverse delta and both boots retained',
             physical_system_written=False,recovery_written=False,both_data_profiles_preserved=True)
(e/'v42-verified-installation-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(p/'CURRENT-STATUS.md').write_text(f'''# Current SM-T110 development state

Updated2026-11-12. **v42-GApps / BOOT48 is installed. Requested logging and memory
defaults are permanent and verified after a fresh boot, without live overrides.**
No build, flash or test remains running. The broader ROM port is unfinished.

## Installed identity and safeguards

- BootID {install['boot_id']}; primary system_server at boot completion302.
- System SHA {install['system_sha256']}.
- BOOT48 SHA {install['boot_sha256']}.
- Bootstrap/system policy SHA {boot['bootstrap_policy_sha256']}.
- Boot completed{install['seconds_to_boot_completed']}s. SELinux Enforcing.
- System remains the read-only userdata loop image. NEVER write physical SYSTEM
  p15. TWRP and both Android data profiles are preserved.
- Immediate complete rollback: v41-GApps/BOOT47. Host full images retained, plus
  forward/reverse delta and both boot images at Android
  /stage-data/local/tmp/t110-v42-persistent-delta
  (TWRP /data/local/tmp/t110-v42-persistent-delta).

## Permanent defaults verified on the tablet

- Init applies swappiness100 with the exact proc_t110_swappiness node label.
  No write denial and no engineering-shell write was needed after reboot.
-512MiB standard compressed swap active; page-cluster0. BOOT47's tested standard
  reclaim kernel and all existing hardware modules are unchanged.
- Periodic full-kernel snapshot writer absent by default. One early kernel
  snapshot61167bytes and boot checkpoints retained for this boot.
- t110-logcat diagnostic file capture never started. Normal Android logd runs.
- Snapshot opt-in fixture passed all5 cases, including invalid marker rejection.
- Complete native selinux_policy build passed85 actions, including freeze,
  compatibility and context checks. No check was disabled. Compiled policy
  introspection confirms the exact node and unchanged permissive-domain set.
- Image filesystem, hashes, file metadata/labels, paired boot policy and device
  write readback checks passed. Only two system SELinux files changed; Google,
  Lineage APKs and all hardware components were retained.

Evidence: evidence/ui-system-hang-20261112/v42-persistence/result.json,
v42-installation.json and v42-verified-installation-summary.json.

## Policy reference audit

The fork already had GPU text-relocation exceptions, a conditional legacy file
swapon permission and4 device-property definitions. Their API33 references had
not been updated. Each exact hunk was checked against Git HEAD and the effective
source, then recorded only in the corresponding4 reference files. Runtime rules
were unchanged by this reference repair. Other API versions were untouched.
See gpu-api-reference-audit.json and patch0106. The only requested new runtime
permission grants init access to the specifically labelled swappiness node.

The native build passed. The initial post-build export tool invocation needed
correction (available checkpolicy, binary MLS mode); checked export then passed.
Raw build log retains that initial export error; the final component manifest and
fresh-boot verification above are authoritative. Do not rerun a build because of
that historical traceback alone.

## Remaining work: no blanket UI/functionality PASS

Earlier v41 interaction tests produced SystemUI and Search ANRs. Owner reported
better responsiveness after live memory tuning and stopping debug writers, still
not perfect. v42 verifies those defaults persist; no new UI stress/finger test
or complete smoothness claim is made. Current last-ANR query had no ANR at its
inspection time, which is not proof of a fully fixed UI.

Native GPU windows and JIT remain disabled pending proper compatibility work.
Search host preopt and standard swap remain active. Native Bluetooth previously
failed lookup qualification; camera provider, audio, sensors, key LEDs and MTP
remain unfinished. Physical microSD/accessory checks remain pending. Radio code
was retained, not newly functionally qualified. Preserve normal Lineage features.
No public push, Gerrit submission or public ROM release was made this turn.
''',encoding='utf-8')
(p/'RESUME-NEXT.md').write_text('''# Next development pass

The requested permanent logging/memory update is DONE: v42-GApps/BOOT48 installed
and verified after a fresh boot. Read CURRENT-STATUS.md. Do not reapply the live
swappiness workaround or restart diagnostic writers automatically.

No pending build/flash/test. Current paired artifacts and verification:
- artifacts/lineage20-rom-v42-gapps/host-verification.json
- artifacts/android13-boot-v48/provenance.json
- evidence/ui-system-hang-20261112/v42-persistence/result.json
- evidence/ui-system-hang-20261112/v42-installation.json

Snapshot logging is opt-in through the root-owned regular periodic-enabled marker;
diagnostic file logcat starts only on explicit init service request. Normal logd
is retained. See PERSISTENT-TUNING.md. Fresh boot needs no manual overrides.

The exact swappiness label/init permission is in canonical device source and E.
API33 reference repair is audited in patch0106; complete freeze/compatibility/
context checks pass. Native build succeeded; an initial exporter invocation
error was corrected and validated export passed. Do not mistake the retained
historical export traceback for a failed native build.

Next scope is actual remaining functionality/UI responsiveness as requested by
the user. Earlier ANRs/lag are not declared fixed. GPU app windows and JIT remain
disabled until compatible. Keep native Lineage/Google apps/features. No more
synthetic boot loops or feature removal to claim responsiveness.

Immediate rollback is v41/BOOT47, with host images and the complete v42 reverse
delta/both boots staged. Never write physical SYSTEM p15 or erase either profile.
Source Android environment is T110Build on E, kernel/tools Ubuntu on C. Export
small verified results before the E distro exits. No subagents.
''',encoding='utf-8')
f=p/'BUILD-WORKSPACE.json';state=json.loads(f.read_text());state.update(state='v42-GApps / BOOT48 installed; permanent logging/memory defaults verified on fresh boot',
 current_installed_system_sha256=install['system_sha256'],current_installed_boot_sha256=install['boot_sha256'],current_installed_boot_id=install['boot_id'],
 active_operation=None,pending_policy_build=None,logging_and_memory_settings_persistent=True,ui_fixed=False,
 current_verification='evidence/ui-system-hang-20261112/v42-persistence/result.json')
f.write_text(json.dumps(state,indent=2)+'\n')
f=p/'FUNCTIONAL-CHECKLIST.md';text=f.read_text(encoding='utf-8')
updates={
 'CORE01':f'**CORE01 Boot reaches Android and launcher - PARTIAL**. v42/BOOT48 boot_completed{install["seconds_to_boot_completed"]}s, Enforcing. Permanent quiet logging and memory defaults verified after fresh boot; no complete UI qualification claimed. [evidence](evidence/ui-system-hang-20261112/v42-persistence/result.json)',
 'CORE02':'**CORE02 Startup completes without service ANRs or automatic restarts - FAIL**. Earlier v41 full interaction tests had SystemUI/Search ANRs. v42 permanently applies the owner-improved logging/memory defaults, but no new full UI stability pass is claimed. [evidence](evidence/ui-system-hang-20261112/v42-verified-installation-summary.json)'}
for key,value in updates.items():
 text,count=re.subn(r'^- \[ \] \*\*'+key+r' .*$', '- [ ] '+value,text,flags=re.M);assert count==1
f.write_text(text,encoding='utf-8')
print('Installed v42/BOOT48 verified and checkpointed; overall UI fix remains unclaimed')
