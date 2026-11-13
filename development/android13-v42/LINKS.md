# T110 development links

2026-11-12. Source checkpoints, not a stable ROM release.

- [Device/bootstrap/patch source and Android7.1 audit](https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/t110/android13-v42-checkpoint)
- [Complete current kernel changes/config checkpoint](https://github.com/Tapuz97/android_kernel_samsung_goya/tree/t110/android13-v42-checkpoint), commit3eb98fe728aefa780638a1bb2f487e19ba6fadcb.
- [Soong Gerrit review513083](https://review.lineageos.org/c/LineageOS/android_build_soong/+/513083), ownerTapuz97/account38571, NEW/unmerged at submission.
- [Original Soong fork branch](https://github.com/Tapuz97/android_build_soong/tree/t110/binder32bit-device-only).
- [Shared-I2C kernel PR](https://github.com/visyone/android_kernel_samsung_goya/pull/1).
- [ION mapping-bounds kernel PR](https://github.com/visyone/android_kernel_samsung_goya/pull/2).
- [Physical keymaps device PR](https://github.com/visyone/android_device_samsung_goyawifi/pull/1).
- [Private draft restoration backup](https://github.com/Tapuz97/android_device_samsung_goyawifi/releases/tag/untagged-318e561e76a42ef76b33). Login with the owner's GitHub account. ReleaseID443063640, draft tag t110-development-backup-20261112. Keep it unpublished: it contains private device logs and proprietary firmware/Google binaries.

See RESTORE.md, ONLINE-BACKUP.md and LINEAGE14-GPU-AND-SLEEP-AUDIT.md before resuming. No XDA public ROM package or guide has been published.

## Fixed preservation tags

- [Device source snapshot](https://github.com/Tapuz97/android_device_samsung_goyawifi/tree/t110-android13-v42-20261112): efe363e0f1358c52c678e41406851b811aad0188.
- [Kernel source snapshot](https://github.com/Tapuz97/android_kernel_samsung_goya/tree/t110-android13-v42-20261112): 3eb98fe728aefa780638a1bb2f487e19ba6fadcb.

Both use tag t110-android13-v42-20261112. The working branch can acquire later
documentation updates; these tags preserve the source checkpoint itself.

## Scoped fixes integrated into our forks - 2026-11-13

- [Kernel: shared-I2C fix](https://github.com/Tapuz97/android_kernel_samsung_goya/commit/d1bb20a92ac9ee2707cd8065059fea525fde26dd).
- [Kernel: ION repair, with shared-I2C ancestor](https://github.com/Tapuz97/android_kernel_samsung_goya/commit/381471a46a9adfed2c447cd925d5a26b9d4e2bf0).
- [Device: physical keymaps](https://github.com/Tapuz97/android_device_samsung_goyawifi/commit/0190671f1bd988f1d59faa2e499e0723fea2f322).

Integrated on the owner forks' lineage-20.0 branches. The three visyone PRs
remain open for their maintainer; our account cannot merge or self-approve them.
See PR-REVIEW-20261113.md for fresh checks and limitations. Preservation tags
and the Android13 checkpoint code were not modified.
