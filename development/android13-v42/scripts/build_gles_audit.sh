#!/bin/bash
set -euo pipefail
base=/root/t110-build
project='/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110'
clang="$base/lineage20/prebuilts/clang/host/linux-x86/clang-r450784d"
mode=${1:-3}
[[ $mode =~ ^[1-6]$ ]]
mkdir -p "$base/gles-audit"
"$clang/bin/clang" --target=armv7a-linux-androideabi33 -fuse-ld=lld \
    -fPIC -shared -nostdlib -O1 -Wall -Wextra -Werror -DT110_AUDIT_RESOLVE_MODE="$mode" \
    -Wl,-soname,libt110_gles_audit.so -Wl,-z,defs \
    -o "$base/gles-audit/libt110_gles_audit.so" "$project/scripts/interaction-audit/gles_audit.c" \
    "$clang/lib64/clang/14.0.6/lib/linux/libclang_rt.builtins-arm-android.a" \
    "$base/stock-system-files/lib/libc.so" "$base/stock-system-files/lib/liblog.so"
# These are linker inputs only. Runtime resolves the public libc/log SONAMEs.
readelf -d "$base/gles-audit/libt110_gles_audit.so" | grep NEEDED
cp "$base/gles-audit/libt110_gles_audit.so" "$project/evidence/hardware-v35/libt110_gles_audit.so"
python3 - "$project" "$mode" <<'PY'
from pathlib import Path
import hashlib,json,sys
p=Path(sys.argv[1]);e=p/'evidence/hardware-v35'
record={'source_sha256':hashlib.sha256((p/'scripts/interaction-audit/gles_audit.c').read_bytes()).hexdigest(),
        'library_sha256':hashlib.sha256((e/'libt110_gles_audit.so').read_bytes()).hexdigest(),
        'target':'armv7a-linux-androideabi33','resolve_mode':int(sys.argv[2]),'diagnostic_preswap_readback':sys.argv[2] in ('2','3','6'),
        'scope':'temporary test APK only; never production apps'}
(e/'gles-audit-build.json').write_text(json.dumps(record,indent=2)+'\n')
PY
