# T110 current checkpoint — 2026-11-12

**Latest instruction:** the owner chose manual deletion of one directory:
C:\Users\Gal\Documents\ChatGPT\Electronic Repair\SM-T110.
The retained information is copied and verified in sibling SM-T110-Notes.
Everything in the original directory may be deleted; do not ask the owner to
rerun cleanup scripts. E: and Ubuntu cleanup are complete. After the owner
deletes it, verify absence from the parent directory without using the deleted
directory as a tool working directory. See this notes folder's README.md.

**Latest:** source audit and online preservation are complete. Nine payloads,
6,299,404,805 bytes, plus the separate proof record were downloaded/hash-verified.
The complete project archive passed all67,743 member hashes. All25 changed
Android project bases were independently verified online. Both forks have
source tag t110-android13-v42-20261112. Soong Gerrit513083 is submitted/unmerged.

Ubuntu:/root/t110-build is removed, trimmed and the VHD compacted. T110Build
was unregistered and E:/T110-build now contains only README.md. Last measured
free space: C121,123,577,856 bytes; E491,912,040,448 bytes.

C: cleanup stopped at an empty locked folder. Automatic review rejected the
subsequent direct empty-folder deletion with "blocked by policy". The owner
was asked to close old cleanup PowerShell/Explorer windows and run:

```powershell
& 'C:\Users\Gal\Documents\ChatGPT\Electronic Repair\SM-T110\scripts\finish_c_cleanup.ps1'
```

The continuation is pushed to the device branch, commit000463e. It retrieves
and verifies the proof, rechecks all nine remote payloads, resets its current
folder and removes the remaining C: data, keeping12 informational Markdown
records. If a lock remains, it preserves itself/proof and writes the pending
result to CLEANUP.md. Verify the filesystem after the owner finishes; do not
claim C: is fully cleaned based on a message alone. Then update/publish the
final Markdown records. Other projects/apps, D: targets and tablet storage
remain outside this cleanup.

No Nougat build, runtime qualification, flash or reboot occurred. Restore
source via LINKS.md/RESTORE.md before resuming the small graphics/power target
described in LINEAGE14-GPU-AND-SLEEP-AUDIT.md. The full ROM build waits for
proper GPU app drawing and physical sleep/wake qualification.

## Superseded archive-progress notes

The notes below describe an earlier point in this task. Their archive jobs
have finished; their session IDs and pending-export statements are historical.

The owner asked for an Android7.1/Lineage14.1 GPU/sleep source audit, preservation/publication of Android13 work, then COMPLETE C/E T110-development cleanup, keeping informative Markdown only. Do not start a full Nougat build or flash the tablet. The owner authorized use of our existing GitHub repository after Gerrit-only archive proved impossible.

## Completed

- Audit: LINEAGE14-GPU-AND-SLEEP-AUDIT.md. Includes HWC1/Marvell EGL+alpha ABI, gralloc0 adapter, conditional textrel/app-target-SDK limitation, panel/touch/system-PM sequence and required gates. No Nougat runtime PASS.
- Gerrit513083 NEW, owner38571/Tapuz97, commit e4b48eb34394c7c2fb1bc882854c91be7860c24c. Temporary token was used only in process memory and is no longer needed.
- Public device branch t110/android13-v42-checkpoint, latest recorded source-checkpoint-publication.json. Public kernel same branch, commit3eb98fe728aefa780638a1bb2f487e19ba6fadcb,118 files /111 existing modified.
- Source exports:1242 projects,25 changed, no missing; dirty bases checked against remote refs and live upstream verification is being completed separately. Full exact kernel plus both host fixture archives saved.
- Private DRAFT release443063640, tag t110-development-backup-20261112 in Tapuz97/android_device_samsung_goyawifi. DO NOT PUBLISH. Anonymous release/asset checks404. Five initial archives and project parts000/001 have full authenticated download SHA256 PASS.
- Obsolete-image pass result confirms36 files /31,662,051,788 bytes removed, no move to D; C free rose to~48.5GiB before new restoration archives.

## Still running / next

- scripts/archive_project_restoration.py: exec session63068. Streams all required remaining C payloads into1792MiB pieces, then verifies EVERY tar member against its source hash. Current pieces000/001 are closed and already uploaded/download-hashed; part002 remains open until this process finishes. Do not upload an open final piece or delete sources.
- scripts/verify_source_bases_online.py: exec session23757; verify all25 changed-project bases via authenticated GitHub commit endpoints (or recorded Gitiles URL).
- Required finalization: upload remaining closed project part(s) only after project-restoration-verification.json PASS; package final metadata/manifests/latest root Markdown/scripts into final-metadata-private.tar.gz; upload and download-hash it too. Update ONLINE-BACKUP.md with all payload sizes/hashes/asset IDs.
- Final source checkpoint update must include the latest audit and cleanup/helper scripts. Existing publisher can append a commit on the checkpoint branch; root source is not a ready-made ROM/device product.
- Generate backups/android13-before-lineage14-20261112/FINAL-ONLINE-VERIFIED.json only after EVERY required asset has download SHA256 PASS, complete project tar readback PASS and both source heads verified online.
- Then execute scripts/cleanup_wsl_t110.py in Ubuntu to remove ONLY /root/t110-build (guarded by final proof); then scripts/final_t110_cleanup.ps1 for dedicated T110Build unregister/E root and C project non-Markdown removal. Ubuntu itself, installed SDK/apps, other projects and D targets remain untouched. E old lineage20.ext4.img is a documented UNVERIFIED obsolete workspace, not active source; actual active distro base is E:/T110-build/WSL.
- If automatic approval review rejects deletion, do not bypass it: record action/reason, retain data and provide the concrete verified cleanup scripts for the owner. Earlier narrower image pass was completed via the saved result despite tool rejections.
- Only AFTER a successful verified teardown should CURRENT-STATUS/CLEANUP/RESUME docs say local sources are removed. Update online Markdown records without re-creating build clutter.

See LINKS.md, RESTORE.md, ACHIEVEMENTS.md, REFERENCES.md. No tablet command, flash or reboot was performed during this audit/archive task.
