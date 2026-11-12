#!/bin/bash
set -eu
base=/root/t110-build
mkdir -p "$base/out-security"
cp "$base/out-baseline/.config" "$base/out-security/.config"
cd "$base/kernel"
scripts/config --file "$base/out-security/.config" \
 -e AUDIT -e SECURITY -e SECURITYFS -e SECURITY_NETWORK \
 -e SECURITY_SELINUX -e SECURITY_SELINUX_BOOTPARAM -e SECURITY_SELINUX_DEVELOP \
 -d DEFAULT_SECURITY_DAC -e DEFAULT_SECURITY_SELINUX --set-str DEFAULT_SECURITY selinux \
 -e EXT4_FS_SECURITY -e TMPFS_XATTR -e TMPFS_POSIX_ACL \
 -e CGROUPS -e CGROUP_DEBUG -e CGROUP_FREEZER -e CGROUP_DEVICE \
 -e CPUSETS -e CGROUP_CPUACCT -e RESOURCE_COUNTERS -e CGROUP_SCHED \
 -e FAIR_GROUP_SCHED -e RT_GROUP_SCHED -e CFS_BANDWIDTH \
 -e IKCONFIG -e IKCONFIG_PROC
yes "" | make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$base/out-security" oldconfig > "$base/logs/security-config.log" 2>&1
make -j4 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$base/out-security" zImage > "$base/logs/security-build.log" 2>&1
sha256sum "$base/out-security/arch/arm/boot/zImage"

