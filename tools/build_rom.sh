#!/bin/bash
# Rebuild only this internal-drive development checkout. Does not contact the tablet.
set -e
set -o pipefail
export PATH=/root/t110-lineage14/host-bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export LC_ALL=C
cd /root/t110-lineage14/android
source build/envsetup.sh >/dev/null
lunch lineage_goyawifi-userdebug >/dev/null
make -j12 systemimage bootimage
