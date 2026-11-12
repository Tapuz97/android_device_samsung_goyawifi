#!/bin/bash
set -eo pipefail
[ "${WSL_DISTRO_NAME:-}" = T110Build ] || exit 3
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
cd "$base/lineage20"
test -s "$base/manifest-pinned.xml"
test "$(findmnt -n -o FSTYPE /)" = ext4
free_kb=$(df -Pk / | awk 'NR==2 {print $4}')
[ "$free_kb" -gt 157286400 ] || { echo 'Less than 150 GiB free'; exit 3; }
mkdir -p "$base/logs" device/samsung
stamp=${T110_SYSTEM_LOG_STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}
[[ "$stamp" =~ ^[0-9]{8}T[0-9]{6}Z$ ]]
log=$base/logs/system-image-$stamp.log
exec > >(tee "$log") 2>&1
echo "Build-only system image; NOT FOR FLASHING. Log: $log"
cp -a "$project/work/device/samsung/t110_bringup" device/samsung/
python3 "$project/scripts/prepare_sd8777_build.py" "$PWD"
for item in 'system/core:0009-android13-t110-legacy-processgroups.patch' 'packages/modules/adb:0013-adbd-t110-synchronous-functionfs.patch' 'build/soong:0015-soong-binder32bit-android-only.patch' 'bionic:0016-linker-t110-vivante-textrel.patch' 'system/sepolicy:0017-sepolicy-t110-vivante-textrel.patch' 'system/core:0019-init-t110-flattened-namespace.patch' 'system/core:0021-init-nonthrowing-fd-diagnostics.patch' 'system/bpf:0022-bpfloader-t110-legacy-kernel.patch' 'system/netd:0023-netd-t110-legacy-startup.patch' 'frameworks/libs/net:0024-bpfmap-pre-ebpf-error-handling.patch' 'packages/modules/Connectivity:0025-connectivity-legacy-qtaguid.patch' 'system/core:0026-init-fatal-reboot-target-length.patch' 'system/sepolicy:0027-sepolicy-t110-compat-property-contexts.patch' 'bionic:0028-bionic-a9-single-register-thumb-store.patch' 'hardware/interfaces:0029-audio-binder-pool-initialization-order.patch' 'build/make:0032-build-allow-device-jit-default-override.patch' 'hardware/interfaces:0064-composer-t110-cached-scanout-staging.patch' 'frameworks/native:0048-gralloc-t110-process-initialization.patch' 'frameworks/native:0065-renderengine-t110-reuse-idle-swap-spares.patch' 'art:0039-art-zygote-visibility-checkpoint-lock.patch' 'frameworks/base:0040-gnss-t110-declared-service-probe.patch' 'system/memory/lmkd:0041-lmkd-accepted-socket-credentials.patch' 'build/soong:0042-soong-t110-flattened-apex-app-preopt.patch' 'build/make:0043-build-t110-standard-art-selection.patch' 'frameworks/base:0045-systemui-empty-active-appops.patch' 'frameworks/av:0046-codec2-ion-error-state-traits.patch' 'frameworks/native:0047-egl-t110-process-initialization.patch' 'packages/modules/Connectivity:0049-networkstats-global-alert-service-errors.patch' 'system/netd:0050-netd-global-alert-commit-on-success.patch' 'external/libfuse:0051-libfuse-unsigned-passthrough-mask.patch' 'packages/apps/SetupWizard:0057-setupwizard-configurable-canvas-rendering.patch' 'frameworks/base:0058-framework-t110-software-window-rendering.patch' 'frameworks/libs/systemui:0059-iconloader-t110-software-bitmaps.patch' 'frameworks/base:0060-systemui-shared-t110-software-task-snapshots.patch' 'frameworks/base:0062-framework-t110-exclusive-navigation.patch' 'packages/apps/LineageParts:0063-lineageparts-t110-navigation-mode-switch.patch' 'frameworks/base:0066-systemui-respect-strictmode-default-optout.patch' 'packages/apps/Trebuchet:0067-trebuchet-t110-software-frame-completion.patch' 'packages/apps/Trebuchet:0068-trebuchet-t110-software-surface-transactions.patch' 'packages/apps/Settings:0069-settings-t110-optional-usb-ethernet.patch' 'packages/apps/Settings:0070-settings-hearing-aid-without-bluetooth.patch' 'frameworks/base:0071-wallpaper-t110-software-crop.patch' 'frameworks/base:0072-systemui-t110-readable-lock-wallpaper.patch' 'frameworks/base:0073-systemui-t110-software-image-wallpaper.patch' 'packages/apps/WallpaperPicker2:0075-wallpaperpicker-t110-readable-bitmaps.patch' 'frameworks/base:0076-systemui-t110-finite-notification-clips.patch' 'lineage-sdk:0077-lineage-sdk-t110-nonblocking-hardware-probes.patch' 'frameworks/native:0078-gralloc-t110-initialize-import-only-clients.patch' 'frameworks/native:0080-gui-t110-retain-capture-buffer-owner.patch' 'frameworks/native:0082-gralloc-t110-isolated-apex-hardware-lookup.patch' 'system/sepolicy:0083-sepolicy-t110-legacy-swap-permission.patch' 'frameworks/av:0084-codec2-t110-standard-yv12-raw-lock.patch'; do
    repo=${item%%:*}
    patch=$project/patches/${item#*:}
    if [[ ${item#*:} == 0042-soong-t110-flattened-apex-app-preopt.patch ]] &&
        git -C "$repo" apply --reverse --check "$project/patches/0086-soong-preopt-selected-t110-tethering-app.patch" >/dev/null 2>&1; then
        continue
    fi
    if [[ ${item#*:} == 0064-composer-t110-cached-scanout-staging.patch ]] &&
        git -C "$repo" apply --reverse --check "$project/patches/0089-composer-t110-neon-scanout.patch" >/dev/null 2>&1; then
        continue
    fi
    if git -C "$repo" apply --reverse --check "$patch" >/dev/null 2>&1; then
        echo "Already applied: ${item#*:}"
    else
        git -C "$repo" apply --check "$patch"
        git -C "$repo" apply "$patch"
    fi
done
python3 "$project/scripts/prepare_startup_and_restart.py" "$PWD"
scanout="$project/patches/0089-composer-t110-neon-scanout.patch"
if ! git -C hardware/interfaces apply --reverse --check "$scanout" >/dev/null 2>&1; then
    git -C hardware/interfaces apply --check "$scanout"
    git -C hardware/interfaces apply "$scanout"
fi
unset ALLOW_MISSING_DEPENDENCIES
python3 "$project/scripts/prepare_soong_memory.py"
export OUT_DIR=$base/out-system
export USE_RBE=false
export T110_SOONG_GOGC=30
export NINJA_HIGHMEM_NUM_JOBS=1
# The legacy kernel does not expose /proc/self/ns/mnt. Use the Android 13
# build mode that keeps APEX content on the system partition in one namespace.
export OVERRIDE_TARGET_FLATTEN_APEX=true
source build/envsetup.sh
lunch lineage_t110_system-eng
m -j"${T110_SYSTEM_JOBS:-2}" systemimage
