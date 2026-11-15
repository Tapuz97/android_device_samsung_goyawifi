#!/bin/bash
set -e
set -o pipefail
export PATH=/root/t110-lineage14/host-bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export LC_ALL=C
export OUT_DIR=/root/t110-lineage14-ui/out
cd /root/t110-lineage14/android
source build/envsetup.sh >/dev/null
lunch lineage_goyawifi-userdebug >/dev/null
export BUILD_NUMBER=T110_UI_20261114_R2
export PATH=/root/t110-lineage14/host-bin:$PATH
# Launcher-only update; do not replace the verified complete R2 ROM artifacts.
make -j4 Trebuchet
