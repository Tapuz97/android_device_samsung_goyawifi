# Next development pass

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
