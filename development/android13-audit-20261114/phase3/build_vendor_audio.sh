#!/bin/bash
set -eo pipefail
cd /root/t110-android13/android
export OUT_DIR=/root/t110-android13/out USE_RBE=false NINJA_HIGHMEM_NUM_JOBS=1
export OVERRIDE_TARGET_FLATTEN_APEX=true GOGC=25 T110_SOONG_GOGC=25
export JAVA_HOME=/root/t110-android13/android/prebuilts/jdk/jdk11/linux-x86
export PATH="$JAVA_HOME/bin:/usr/local/bin:/usr/bin:/bin"
export BUILD_NUMBER=t110_phase3_20261114
set +u
source build/envsetup.sh
lunch lineage_t110_system-eng
mapfile -t audio_modules < <(python3 -c 'import json;print("\n".join(json.load(open("/root/t110-android13-audit/vendor-audio-targets.json"))))')
product_out="$OUT_DIR/target/product/t110_bringup"
mapfile -t audio_config_targets < <(python3 - <<'PY'
from pathlib import Path
base = Path('/root/t110-android13/out/target/product/t110_bringup')
mk = Path('device/samsung/t110_bringup/audio/vendor-audio.mk').read_text()
for line in mk.splitlines():
    if 'device/samsung/t110_bringup/audio/config/' in line:
        dest = line.strip().rstrip('\\').strip().split(':', 1)[1]
        dest = dest.replace('$(TARGET_COPY_OUT_VENDOR)', 'system/vendor')
        dest = dest.replace('$(TARGET_COPY_OUT_SYSTEM)', 'system')
        assert '$(' not in dest, dest
        print(base / dest)
PY
)
m -j8 "${audio_modules[@]}" "${audio_config_targets[@]}" \
    "$product_out/system/vendor/lib/libt110_audio_legacy_compat.so" \
    "$product_out/system/vendor/bin/t110_legacy_libc_probe" \
    "$product_out/system/vendor/etc/audio_policy_configuration.xml" \
    "$product_out/system/vendor/etc/primary_audio_policy_configuration.xml" \
    "$product_out/system/vendor/etc/r_submix_audio_policy_configuration.xml" \
    "$product_out/system/vendor/etc/audio_policy_volumes.xml" \
    "$product_out/system/vendor/etc/default_volume_tables.xml" \
    "$product_out/system/vendor/etc/surround_sound_configuration_5_0.xml" \
    "$product_out/system/vendor/etc/init/init.t110.audio.rc" \
    "$product_out/system/bin/surfaceflinger" \
    "$product_out/system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service" \
    android.hardware.graphics.allocator@2.0-impl android.hardware.graphics.mapper@2.0-impl
printf '\nT110_VENDOR_AUDIO_BUILD_PASS\n'
