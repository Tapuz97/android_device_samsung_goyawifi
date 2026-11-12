#!/bin/bash
set -eu
cd /root/t110-build/lineage20
# Deliberately limited native-userspace checkout, not a full ROM sync.
free_kb=$(df -Pk /mnt/c | awk 'NR==2 {print $4}')
[ "$free_kb" -gt 31457280 ] || { echo 'Need at least 30 GiB host free before this batch'; exit 3; }
.repo/repo/repo sync -c -j4 --no-clone-bundle --no-tags --fail-fast \
 build/bazel build/bazel_common_rules build/pesto \
 prebuilts/build-tools prebuilts/go/linux-x86 prebuilts/clang/host/linux-x86 prebuilts/clang-tools \
 prebuilts/bazel/linux-x86_64 prebuilts/jdk/jdk11 prebuilts/rust \
 external/avb external/boringssl external/fmtlib external/googletest external/libcap \
 external/libcxx external/libcxxabi external/libxml2 external/pcre external/protobuf external/zlib \
 external/lz4 external/xz-embedded external/zstd external/e2fsprogs external/f2fs-tools \
 external/squashfs-tools external/selinux system/unwinding external/compiler-rt \
 external/python/markupsafe external/python/jinja external/python/six \
 system/extras system/tools/aidl system/tools/hidl system/tools/mkbootimg system/tools/sysprop \
 system/sepolicy system/security system/hardware/interfaces system/libvintf system/libziparchive \
 system/linkerconfig system/apex system/gsid system/update_engine \
 packages/modules/adb packages/modules/SdkExtensions \
 hardware/libhardware hardware/libhardware_legacy hardware/interfaces \
 vendor/lineage device/lineage/sepolicy development
