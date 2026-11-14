#!/bin/bash
set -euo pipefail
cd /root/t110-android13/android
export OUT_DIR=/root/t110-android13/out
export USE_RBE=false NINJA_HIGHMEM_NUM_JOBS=1 OVERRIDE_TARGET_FLATTEN_APEX=true
export GOGC=25 T110_SOONG_GOGC=25
export JAVA_HOME=/root/t110-android13/android/prebuilts/jdk/jdk11/linux-x86
export PATH="$JAVA_HOME/bin:/usr/local/bin:/usr/bin:/bin"
export BUILD_NUMBER=t110_phase3_20261114
mkdir -p /root/t110-android13/logs
set +u
source build/envsetup.sh
lunch lineage_t110_system-eng
product_out="$OUT_DIR/target/product/t110_bringup"
# Installed ARM targets avoid unrelated desktop layoutlib/HWUI variants while
# compiling/linking each complete production library and its dependencies.
m -j8 "$product_out/system/lib/libhwui.so" "$product_out/system/lib/libgui.so" \
    linker "$product_out/system/vendor/lib/hw/audio.primary.t110.so" \
    "$product_out/system/vendor/lib/libt110_audio_legacy_compat.so" \
    "$product_out/system/vendor/lib/hw/android.hardware.audio@7.1-impl.so" \
    "$product_out/system/vendor/lib/hw/android.hardware.audio.effect@7.0-impl.so" \
    "$product_out/system/vendor/bin/hw/android.hardware.audio.service" \
    selinux_policy sepolicy_tests sepolicy_freeze_test
printf '\nT110_FULL_COMPONENT_BUILD_PASS\n'
