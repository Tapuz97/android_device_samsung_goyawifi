#!/bin/bash
set -eo pipefail
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
out=/root/t110-build/out-native/soong/.intermediates
variant=android_recovery_arm_armv7-a-neon_cortex-a9
bash "$project/scripts/build_native_bootstrap.sh" init_first_stage \
  "$out/system/core/init/init_second_stage/$variant/init" \
  "$out/packages/modules/adb/adbd/$variant/adbd" \
  "$out/external/mksh/sh/$variant/sh" \
  "$out/external/toybox/toybox/$variant/toybox" \
  "$out/system/core/toolbox/toolbox/$variant/toolbox" \
  sepolicy.recovery plat_file_contexts.recovery plat_property_contexts.recovery \
  t110_recovery_watchdog host_init_verifier
