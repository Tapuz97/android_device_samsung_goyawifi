from pathlib import Path
import hashlib
import json
import subprocess

source = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/android13-audit')
android = Path('/root/t110-android13/android')
audit = Path('/root/t110-android13-audit')
out = audit / 'namespace-tools'
out.mkdir(exist_ok=True)
serializer = android / 'system/core/property_service/libpropertyinfoserializer'
parser = android / 'system/core/property_service/libpropertyinfoparser'
# Compile the exact pinned upstream serializer/parser implementation natively.
# This avoids linking libstdc++ against Soong's libc++ archives or using a
# hand-written binary property-area format.
host_sources = [source / 'BuildCandidatePropertyInfo.cpp'] + [serializer / n for n in (
    'property_info_file.cpp', 'property_info_serializer.cpp', 'trie_builder.cpp', 'trie_serializer.cpp')]
host_sources += [parser / 'property_info_parser.cpp', android / 'system/libbase/strings.cpp',
                 android / 'system/libbase/stringprintf.cpp']
host_cmd = ['g++', '-std=c++17', '-O2', '-include', 'algorithm', '-include', 'cstring',
            '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections',
            '-I'+str(serializer / 'include'), '-I'+str(parser / 'include'),
            '-I'+str(android / 'system/libbase/include')]
subprocess.run(host_cmd + [str(p) for p in host_sources] + ['-o', str(out / 'candidate-property-info')], check=True)

legacy = Path('/root/t110-lineage14/android')
ndk = legacy / 'prebuilts/ndk/current/platforms/android-23/arch-arm/usr/lib'
gcc = next(Path('/root/t110-lineage14/toolchains/arm-linux-androideabi-4.6').glob('lib/gcc/arm-linux-androideabi/*/libgcc.a'))
flags = ['clang', '--target=armv7a-linux-androideabi', '-std=c11', '-fno-builtin', '-fPIE',
         '-Wall', '-Wextra', '-Werror', '-I'+str(audit / 'arm-headers')]
for p in ('bionic/libc/include', 'bionic/libc/arch-arm/include', 'bionic/libc/kernel/uapi', 'bionic/libc/kernel/uapi/asm-arm'):
    flags += ['-isystem', str(legacy / p)]
obj = out / 'CandidateNamespaceProbe.o'
subprocess.run(flags + ['-c', str(source / 'CandidateNamespaceProbe.c'), '-o', str(obj)], check=True)
providers = Path('/root/t110-android13/out/target/product/t110_bringup/system/lib/bootstrap')
link_cmd = ['clang', '--target=armv7a-linux-androideabi', '-fuse-ld=lld', '-pie', '-nostdlib',
            '-Wl,--no-undefined', '-Wl,-dynamic-linker,/system/bin/linker', str(ndk / 'crtbegin_dynamic.o'),
            str(obj), '-L'+str(providers), '-lc', '-lm', '-ldl', str(gcc), str(ndk / 'crtend_android.o'),
            '-o', str(out / 'candidate-namespace-probe')]
subprocess.run(link_cmd, check=True)
records = [dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in host_sources]
(out / 'toolchain.json').write_text(json.dumps(dict(host_sources=records, host_flags=host_cmd,
    arm_compile_flags=flags, arm_link=link_cmd, production_payload=False), indent=2) + '\n')
print('Built pinned property serializer and ARM Bionic property/namespace fixture probe; no production source changed.')
