# v18 system: combined offline startup corrections

The three failures from the v26/v17 hardware test were traced to source and addressed in one candidate. This build is offline verified and has not been flashed or booted. It reuses the existing v26 BOOT because its kernel, early policy and classpath remain compatible; no duplicate boot package was created.

## Corrections

- **Setup/Wi-Fi service:** the tablet product lacked `android.hardware.wifi.xml`. SystemServer gates WifiService startup on that feature, even though its service JAR was already installed. The feature declaration is now included. The radio HAL remains unported; this addresses the missing framework service, not wireless connectivity certification.
- **Network statistics:** patch0049 catches netd's ServiceSpecificException during optional global-alert registration, retaining scheduled polling and provider callbacks. Patch0050 commits the netd quota state only when the kernel operation succeeds, so failed insertion no longer leads to updating an absent quota entry.
- **Emulated storage:** saved kernel logs show Samsung sdcardfs rejecting the modern `fsuid` option. The product now sets `external_storage.sdcardfs.enabled=false`, selecting the existing MediaProvider FUSE implementation. No data formatting, direct app access to raw media, or unsupported ext4 quota/casefold enable was introduced.
- **FUSE initialization:** patch0051 makes both bit31 passthrough masks unsigned. Host sanitizers exposed the signed-shift issue; the corrected protocol exchange passes with sanitizer recovery disabled.

Android documents its [MediaProvider FUSE storage path](https://source.android.com/docs/core/storage/scoped) and the separate [SDCardFS replacement concerns](https://source.android.com/docs/core/storage/sdcardfs-deprecate). This candidate selects the existing FUSE path for the current unencrypted test data; it does not adopt modern filesystem casefold/quota configuration or claim full storage compatibility from a host test.

## Validation and limits

Full ARM system build completed: `system-image-20261107T104621Z.log`. Host tests use production Java/native method bodies for network error/retry state and callback retention. The complete pinned libfuse library plus MediaProvider's actual initialization callback exchanged FUSE7.18 requests over a socketpair with this kernel's advertised flags. No host filesystem was mounted and no Android system was booted. Final ASan/UBSan checks pass; an earlier protocol result with recoverable UBSan warnings was superseded and preserved in the evidence folder. The initial ARM build was stopped before input edits, then resumed with all corrections together.

The exported filesystem passed read-only ext4 checks, exact partition fit, native-to-Windows SHA256 comparison, actual network-service DEX catch-handler inspection, Wi-Fi XML and storage-property checks. Existing codec/EGL/gralloc, SystemUI, keystore, framework and display binaries were retained. The new system's compiled policy and root classpath match the existing v26 BOOT.

- Raw system size: 1,594,884,096 bytes.
- System SHA256: `b63c81f908b6147a83d4eab33e3d4fec176a345ed987f3fcf221ae80bbdf23ba`
- System MD5: `40b250a4afe35086bd6ab7610300ce24`
- Existing v26 BOOT SHA256: `d74618b0fb22aec87f2a2309df88cbf8db2bd7dcd51280d72d9fa703ec6099fd`
- Pair manifest: `artifacts/lineage20-rom-v18/rom-pair.json`.
- Evidence: `evidence/offline-v27/contents.json`, `regressions.json`, DEX inspection and sanitizer logs.

The last hardware result remains the failed v26/v17 test. The tablet was last confirmed in TWRP; it was not accessed during this pass. A later full boot must establish setup completion, storage mounting, sustained system_server stability and actual screen/touch behavior. No working-ROM or working-Wi-Fi claim is made.
