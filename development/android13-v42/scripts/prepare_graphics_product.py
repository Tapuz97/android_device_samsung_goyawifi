"""Install the verified T110 graphics blobs and product integration in the build tree."""
import hashlib
from pathlib import Path
import shutil
import subprocess

PROJECT = Path(__file__).resolve().parents[1]
DEVICE = PROJECT / "work/device/samsung/t110_bringup"
STOCK = PROJECT / "stock/T110XXUANI7/system/lib"
DEST = DEVICE / "graphics"
DEST.mkdir(exist_ok=True)
files = {
    "libGAL.so": STOCK / "libGAL.so",
    "libgputex.so": PROJECT / "artifacts/egl-probe/libgputex.so",
    "libgcu.so": STOCK / "libgcu.so",
    "libHWComposerGC.so": STOCK / "libHWComposerGC.so",
    "libstdc++.so": PROJECT / "artifacts/egl-probe/libstdc++.so",
    "egl/libEGL_MRVL.so": STOCK / "egl/libEGL_MRVL.so",
    "egl/libGLESv1_CM_MRVL.so": STOCK / "egl/libGLESv1_CM_MRVL.so",
    "egl/libGLESv2_MRVL.so": STOCK / "egl/libGLESv2_MRVL.so",
    "hw/gralloc.mrvl.so": STOCK / "hw/gralloc.mrvl.so",
    "hw/hwcomposer.mrvl.so": STOCK / "hw/hwcomposer.mrvl.so",
}
bp = ['// Proprietary libraries from the verified SM-T110 stock firmware.\n']
modules = []
inventory = []
for relative, source in files.items():
    target = DEST / relative
    target.parent.mkdir(exist_ok=True)
    shutil.copyfile(source, target)
    module = "t110_" + target.stem.replace(".", "_").replace("+", "p")
    modules.append(module)
    install_dir = Path(relative).parent.as_posix()
    directory = f'    relative_install_path: "{install_dir}",\n' if install_dir != "." else ""
    bp.append(
        'cc_prebuilt_library_shared {\n'
        f'    name: "{module}",\n    stem: "{target.stem}",\n'
        f'    srcs: ["{relative}"],\n'
        '    vendor: true,\n    compile_multilib: "32",\n'
        + directory +
        '    strip: { none: true },\n'
        '    check_elf_files: false,\n'
        '    shared_libs: [],\n'
        '}\n'
    )
    inventory.append(f"{hashlib.sha256(target.read_bytes()).hexdigest()}  {relative}")
shutil.copyfile(PROJECT / "scripts/t110_gralloc_binder_compat.c", DEST / "binder_compat.c")
bp.append('''cc_library_shared {
    name: "libt110_gralloc_binder_compat",
    vendor: true,
    srcs: ["binder_compat.c"],
    shared_libs: ["libbinder"],
    stl: "none",
    cflags: ["-Wall", "-Wextra", "-Werror"],
}
''')
(DEST / "Android.bp").write_text("\n".join(bp))
(DEST / "SHA256SUMS").write_text("\n".join(inventory) + "\n")
modules += [
    "libt110_gralloc_binder_compat",
    "android.hardware.graphics.composer@2.1-service",
    "android.hardware.graphics.allocator@2.0-service",
    "android.hardware.graphics.allocator@2.0-impl",
    "android.hardware.graphics.mapper@2.0-impl",
]
(DEVICE / "graphics.mk").write_text(
    "PRODUCT_PACKAGES += \\\n    " + " \\\n    ".join(modules) + "\n"
    "PRODUCT_VENDOR_PROPERTIES += ro.hardware.egl=MRVL ro.hardware.gralloc=mrvl\n"
    "PRODUCT_SYSTEM_PROPERTIES += ro.t110.legacy_gpu=true\n"
)
print("Prepared", len(files), "stock libraries and graphics services")
