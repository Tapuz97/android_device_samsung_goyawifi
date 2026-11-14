#!/bin/bash
set -eo pipefail
cd /root/t110-android13/android
export OUT_DIR=/root/t110-android13/out
export USE_RBE=false NINJA_HIGHMEM_NUM_JOBS=1 OVERRIDE_TARGET_FLATTEN_APEX=true
export GOGC=25 T110_SOONG_GOGC=25
export JAVA_HOME=/root/t110-android13/android/prebuilts/jdk/jdk11/linux-x86
export PATH="$JAVA_HOME/bin:/usr/local/bin:/usr/bin:/bin"
export BUILD_NUMBER=t110_phase3_20261114
source build/envsetup.sh
lunch lineage_t110_system-eng
# Preserve the already-tested component build identity and cached artifacts.
# Build the host generator too, to inspect the actual candidate's namespaces.
m -j12 systemimage "$OUT_DIR/host/linux-x86/bin/linkerconfig"
printf '\nT110_COMPLETE_SYSTEMIMAGE_BUILD_PASS\n'
