#!/bin/bash
set -e
set -o pipefail
export PATH=/root/t110-lineage14/host-bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export LC_ALL=C
export OUT_DIR=/root/t110-lineage14-ui/out
export BUILD_NUMBER=T110_UI_20261114_R2
# Prebuilt-kernel targets still require the matching exported UAPI headers.
# Generate them into this isolated output, as in the original bring-up.
mkdir -p /root/t110-lineage14-ui/kernel-headers
make -C /root/t110-lineage14/kernel-initramfs-source \
    O=/root/t110-lineage14-ui/kernel-headers ARCH=arm \
    INSTALL_HDR_PATH="$OUT_DIR/target/product/goyawifi/obj/KERNEL_OBJ/usr" \
    headers_install
cd /root/t110-lineage14/android
source build/envsetup.sh >/dev/null
lunch lineage_goyawifi-userdebug >/dev/null
export BUILD_NUMBER=T110_UI_20261114_R2
# envsetup/lunch prepends the JDK and otherwise bypasses the already qualified
# localhost-only Jack launcher/security wrapper.
export PATH=/root/t110-lineage14/host-bin:$PATH
# User interface and framework only. Reuse the verified boot image and kernel.
make -j8 systemimage
