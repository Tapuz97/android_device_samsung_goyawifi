# Current SM-T110 development state


<!-- cleanup-live-start -->
## Cleanup completed — 2026-11-12

All required source, current/rollback images, firmware and evidence were backed
up online and verified before teardown. The large C: and E: project/build
payloads are removed. The dedicated T110Build distro is unregistered; Ubuntu's
T110 build tree is removed and its virtual disk compacted. Ubuntu itself remains.

The remaining original SM-T110 folder was successfully moved to the Windows
Recycle Bin after the owner closed the idle WindowsPackageManagerServer.exe
process holding its empty cleanup subfolder open. Native Windows result:
HRESULT 0x00000000, Aborted=False. The original SM-T110 path is now absent.
All 13 separate retained Markdown records passed unchanged SHA256 checks during
that operation. The final recycled remainder was 889 files / 8,905,498 bytes.
The Recycle Bin was not emptied; this last small remainder is recoverable there.

Only the sibling SM-T110-Notes directory is retained for this project on C:.
It contains 13 Markdown information records and no non-Markdown files. E: was
safely ejected, is currently absent, and may remain physically disconnected.
No unrelated projects, D: targets or tablet files were changed in this continuation.
No Android build, flash or test was started. Cleanup is complete; development
can resume later by restoring the online sources and following the Android7.1
GPU and sleep/wake audit gates.

This result supersedes all older manual-delete/script/pending-lock instructions.
Permanent deletion had been rejected by automatic approval review; the allowed
reversible Recycle Bin operation completed after the Windows lock was released.
<!-- cleanup-live-end -->

## Historical checkpoint details (cleanup instructions below are superseded)

## Development checkpoint and archive work — 2026-11-12



**Latest host cleanup:** all nine restoration payloads and the separate proof

record passed online download/SHA256 checks. Both forks have fixed source tag

t110-android13-v42-20261112. Ubuntu:/root/t110-build is removed/trimmed and its

VHD compacted. T110Build is unregistered; E:/T110-build has only README.md.

The C: pass stopped at a locked empty cleanup folder; automatic review rejected

the subsequent empty-folder command with "blocked by policy". The owner has

the guarded local continuation scripts/finish_c_cleanup.ps1, pushed in device

commit000463e. Verify CLEANUP.md and actual root entries before marking C: complete.

See ONLINE-BACKUP.md, LINKS.md and RESTORE.md. No tablet action occurred here.



Android7.1/Lineage14.1 source audit completed; no Nougat build, flash or hardware qualification. See LINEAGE14-GPU-AND-SLEEP-AUDIT.md. Current Android13 remains physically unqualified despite its previous persistence checks.



The accumulated device/bootstrap/patch source is pushed to the owner's device fork branch t110/android13-v42-checkpoint. The tested Soong Binder32bit fix is submitted to LineageOS Gerrit change513083, status NEW (not merged). Full kernel checkpoint and private restoration archive verification are tracked separately.



The owner requested a complete online backup followed by removing local T110 development files on C/E, keeping informational Markdown. No final teardown is allowed until every required online asset passes authenticated download hash verification. The unrelated files/drives/projects are excluded.



Updated2026-11-12. **v42-GApps / BOOT48 is installed. Requested logging and memory

defaults are permanent and verified after a fresh boot, without live overrides.**

No build, flash or test remains running. The broader ROM port is unfinished.



**Later owner report:** tablet remains physically black/unresponsive despite ADB connectivity. Wake-only request changed logical Asleep to Awake; owner still saw black. Subsequent display OFF/brightness0 may include timeout, so the precise wake/display cause is unproven. v42 is not a usable-ROM pass. See OLDER-ANDROID-ASSESSMENT.md and evidence/v42-owner-unresponsive. User is reconsidering an older Android target; no new flash/reboot performed.





## Installed identity and safeguards



- BootID 6d07c212-787a-430c-8d2b-fede0573bb90; primary system_server at boot completion302.

- System SHA aac99e674a85bc94dab1f794e81501a35c2b3958188a2f0a985717a5ddbeeb16.

- BOOT48 SHA 09da369cd22d09e1b59b70ce273fa305c96cc83bc83bca8a48132737763d3690.

- Bootstrap/system policy SHA 5475f135b9ba02358c36962a48cb726a397569c3e7ee94ec53b916a6f30841ab.

- Boot completed229.66s. SELinux Enforcing.

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

The earlier snapshot made no publication; the development-checkpoint section above records later source and Gerrit publication. No public ROM release has been published.

