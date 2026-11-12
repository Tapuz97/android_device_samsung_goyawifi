# Reassess the Android target after the black-screen report

2026-11-12. Owner reports no physical response/black screen on installed v42.
ADB is connected, same boot6d07c212-787a-430c-8d2b-fede0573bb90, boot_completed1.
Battery reports99%. PowerManager initially reported Asleep, then Awake after a
WAKEUP-only input. Owner still saw black. A later capture found display OFF and
panel brightness0; the gap may include an ordinary screen timeout. Therefore do
not equate logical Awake with a physically recovered panel, or claim a specific
driver root cause from those snapshots alone. One Home request was sent. No
reboot, wipe or replacement ROM flash was performed during this assessment.

The permanent logging/memory checks remain valid, but do not establish usability.
Current app GPU rendering and JIT are disabled, with earlier recurring UI ANRs.
Continuing Android13 as the only target is not justified merely by boot completion.

Recommended next target to AUDIT is Android7.1/LineageOS14.1, not a claim of an
available working SM-T110 image. Its ART JIT source uses ashmem-backed mappings
by default, unlike the modern dual-view memfd path currently blocking this port.
That removes one concrete compatibility burden; GPU/HAL support and actual
performance still require proof on this hardware before a full OS build.

Primary source: https://raw.githubusercontent.com/LineageOS/android_art/cm-14.1/runtime/jit/jit_code_cache.cc

Actual T110-specific existing source found is CM11/Android4.4. It is a useful
lower hardware baseline, not evidence of a complete stable modern ROM:
https://github.com/T110-android/android_device_samsung_goyawifi/tree/cm-11.0
https://github.com/AndroidGoya/android_device_samsung_goya/tree/cm-11.0

Do not infer stable Android6 from the T210 donor name: its own README says its
tree is incomplete and should contain files for recovery. Do not use T113/T113NU
ROMs as T110 evidence; those are different device targets. No verified ready-made
stable T110 Lineage14.1 build was established in this search.

Next decision gate: prove native GPU app drawing, touch and sleep/wake on the
older architecture before committing another large source sync/full build.
Keep the Android13 artifacts/data/rollback intact until a replacement is chosen.
Older Android also narrows modern application support and has obsolete security;
version reduction alone is not proof that hardware acceleration will work.
