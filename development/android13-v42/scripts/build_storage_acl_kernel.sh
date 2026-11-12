#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
src="$base/kernel-binder-secctx"
out="$base/out-storage-acl"
test ! -e "$out"
cmp "$base/out-binder-secctx/.config" "$project/artifacts/kernel-binder-secctx/kernel.config"
cp -a --reflink=auto "$base/out-binder-secctx" "$out"
cd "$src"
scripts/config --file "$out/.config" -e EXT4_FS_POSIX_ACL
make ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" oldnoconfig > "$base/logs/storage-acl-config.log" 2>&1
python3 - "$project/artifacts/kernel-binder-secctx/kernel.config" "$out/.config" <<'PY'
from pathlib import Path
import sys
old, new = [Path(name).read_text() for name in sys.argv[1:]]
assert new == old.replace('# CONFIG_EXT4_FS_POSIX_ACL is not set', 'CONFIG_EXT4_FS_POSIX_ACL=y')
PY
make -j2 ARCH=arm CROSS_COMPILE="$base/toolchain/bin/arm-eabi-" O="$out" zImage modules > "$base/logs/storage-acl-build.log" 2>&1
echo STORAGE_ACL_KERNEL_BUILD_PASS
