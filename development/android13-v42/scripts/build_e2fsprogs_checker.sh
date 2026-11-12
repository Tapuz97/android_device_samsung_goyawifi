#!/bin/bash
set -euo pipefail
base=/root/t110-build/host-tools
mkdir -p "$base"
cd "$base"
url=https://www.kernel.org/pub/linux/kernel/people/tytso/e2fsprogs/v1.47.3
curl -fL "$url/e2fsprogs-1.47.3.tar.xz" -o e2fsprogs-1.47.3.tar.xz
curl -fL "$url/sha256sums.asc" -o e2fsprogs-1.47.3-sha256sums.asc
grep -E '^[0-9a-f]{64}.*e2fsprogs-1.47.3.tar.xz$' e2fsprogs-1.47.3-sha256sums.asc | sha256sum -c -
test ! -e e2fsprogs-1.47.3
tar xf e2fsprogs-1.47.3.tar.xz
cd e2fsprogs-1.47.3
./configure --disable-nls > "$base/e2fsprogs-build.log" 2>&1
make -j2 >> "$base/e2fsprogs-build.log" 2>&1
./e2fsck/e2fsck -V
