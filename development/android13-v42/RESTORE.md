# Restore the T110 development checkpoint

The tablet was not reflashed during this audit/backup task. Its installed Android13 v42/BOOT48 remains unfinished. Keep physical SYSTEM p15 untouched. This is a development checkpoint, not a public install package.

## Download and verify

Sign in to GitHub CLI as Tapuz97 (or a writer on the device repository). Download the unpublished draft assets:

```powershell
gh release download t110-development-backup-20261112 --repo Tapuz97/android_device_samsung_goyawifi --dir T110-restore
```

Use the complete filenames, byte counts and SHA256 values in ONLINE-BACKUP.md. Every required payload must match before extraction. The original online verification downloaded and hashed each asset, not just its API metadata. Draft assets returned404 without authentication. Do not publish the draft.

## Archive roles

- android13-current-private.tar.gz: current v42 raw system/BOOT48 plus canonical local work, patches, scripts and checkpoint records.
- kernel-source-private.tar.gz: full exact working kernel source and tested configuration; use the public kernel checkpoint branch for a clean Git checkout.
- lineage20-source-delta-private.tar.gz: all1242 pinned project revisions,25 changed projects, untracked source and the complete custom t110_bringup product.
- T110Build-host-fixtures-private.tar.gz and Ubuntu-host-fixtures-private.tar.gz: unique native/QEMU/build helpers, source, logs and installed-package version lists outside the main source trees.
- project-restoration-private.tar.gz.part000 and following parts: ONE continuous gzip/tar stream, split for GitHub asset-size limits. Contains the original firmware ZIP, recovery/original-device backups, v41 rollback, saved evidence, local sources, scripts and documentation.
- final-metadata-private.tar.gz: authoritative final checkpoint, manifests, metadata and the newest operator scripts. Extract it last.

Join the numbered project parts in order; never extract each part independently. In Linux/WSL, from the download directory:

```sh
mkdir -p restored
cat project-restoration-private.tar.gz.part* | tar -xz -C restored
tar -xzf android13-current-private.tar.gz -C restored/SM-T110
```

Extract the remaining source/helper archives into separate directories to inspect them; their layouts are described by their archived manifests. The firmware CODE tar and sparse system were redundant extractions of the retained original ZIP; reproduce them from that ZIP if needed. Versioned obsolete image exports were summarized and their metadata retained; do not recreate them as prerequisites.

## Resume source development

Public device work: branch t110/android13-v42-checkpoint in Tapuz97/android_device_samsung_goyawifi, under development/android13-v42. Public kernel work: the same branch name in Tapuz97/android_kernel_samsung_goya. Public copies redact serial/CID/MAC identifiers; private originals are in the archives.

To recreate Android13, initialize repo against the recorded Lineage20 manifest source, select the archived pinned manifest, sync those exact revisions, apply each source-delta/patches/<project>.patch to its matching project, restore untracked/<project>/ files and the custom-product/t110_bringup directory. Check every patch against its recorded HEAD before applying. Build outputs, old kernel clones, package caches and compiler objects are reproducible and were not treated as unique work. Do not treat a pinned manifest alone as the local source changes: restore both.

The full kernel configuration is also in the public kernel branch at arch/arm/configs/t110_android13_v42_defconfig. The validated kernel SHA is b9409c55499df551ecd960f38a5f313304c6ca9e4d3f81c77243fda72a2ed8a6. The GCC4.6 toolchain provenance and build commands are in the archived scripts/records.

For Android7.1, follow LINEAGE14-GPU-AND-SLEEP-AUDIT.md. Do not build the complete product until GPU app drawing and physical panel/touch/system sleep-wake gates pass. QEMU does not emulate the T110 GPU or wake wiring. No new flash or boot experiment is authorized merely by restoring these files.

## Device rollback identities

Current system aac99e674a85bc94dab1f794e81501a35c2b3958188a2f0a985717a5ddbeeb16; BOOT48 09da369cd22d09e1b59b70ce273fa305c96cc83bc83bca8a48132737763d3690.

Rollback system a4e11ac1a749ae31f43118d1a0080a0dff7290ed30e2a3b0583467e4a03e114f; BOOT47 553f292654a703cb259c3e77bd77370e1c6b968f13e86ce886b3d4caa8e2b085. Preserve the userdata loop-image layout, installed recovery and both data profiles. Refer to the original bootstrap/install scripts after verification; these hashes are not instructions to write physical SYSTEM.
