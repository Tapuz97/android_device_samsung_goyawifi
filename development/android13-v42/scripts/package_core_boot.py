"""Package the staged LineageOS core boot and its QEMU equivalent. Run in Ubuntu."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile


PROJECT = Path(__file__).resolve().parents[1]
INPUT = PROJECT / "work/core-boot"
TEMPLATE = PROJECT / "artifacts/android13-ramdisk-v5/boot.img"
BOOT_BYTES = 16 * 1024 * 1024
KERNEL_SHA256 = "ccbb784dc305c0e9134d432d02afaf873fde507cb5d501545e014dfe386458a3"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def boot_image(ramdisk, replacement_kernel=None, fatal_recovery=False):
    template = TEMPLATE.read_bytes()
    assert template[:8] == b"ANDROID!"
    kernel_size, _, old_size, _, second_size, _, _, page, dt_size, _ = struct.unpack_from(
        "<10I", template, 8
    )
    assert (page, second_size, dt_size) == (2048, 0, 0)

    def pad(data):
        return data + bytes(-len(data) % page)

    def image_id(kernel, rd):
        digest = hashlib.sha1()
        for data in (kernel, rd, b""):
            digest.update(data)
            digest.update(struct.pack("<I", len(data)))
        return digest.digest() + bytes(12)

    kernel = template[page:page + kernel_size]
    assert sha256(kernel) == KERNEL_SHA256
    old_offset = page + len(pad(kernel))
    old_rd = template[old_offset:old_offset + old_size]
    assert old_offset + len(pad(old_rd)) == len(template)
    assert template[576:608] == image_id(kernel, old_rd)
    if replacement_kernel is not None:
        kernel = replacement_kernel
    header = bytearray(template[:page])
    if fatal_recovery:
        command = bytes(header[64:576]).split(b"\0", 1)[0]
        command = (command + b" androidboot.init_fatal_reboot_target=recovery").strip()
        assert len(command) < 512
        header[64:576] = command.ljust(512, b"\0")
    struct.pack_into("<I", header, 8, len(kernel))
    struct.pack_into("<I", header, 16, len(ramdisk))
    header[576:608] = image_id(kernel, ramdisk)
    image = bytes(header) + pad(kernel) + pad(ramdisk)
    assert len(image) <= BOOT_BYTES
    return image


def ramdisk(environ_rc, qemu, full=False, module=None):
    with tempfile.TemporaryDirectory(prefix="t110-core-") as scratch:
        root = Path(scratch)
        for directory in (
            "acct", "apex", "config", "data", "data_mirror", "debug_ramdisk", "dev",
            "linkerconfig", "mnt", "odm", "odm_dlkm", "oem", "postinstall", "proc",
            "second_stage_resources/system/etc/ramdisk", "stage-config", "stage-data",
            "stage-system", "storage",
            "sys", "system", "system_dlkm", "vendor_dlkm",
        ):
            (root / directory).mkdir(parents=True)
        for name, target in {
            "bin": "/system/bin",
            "cache": "/data/cache",
            "etc": "/system/etc",
            "product": "/system/product",
            "sdcard": "/storage/self/primary",
            "system_ext": "/system/system_ext",
            "vendor": "/system/vendor",
        }.items():
            if full and name in ("product", "system_ext"):
                # stage.c binds these read-only partition aliases before init.
                # Real mount roots keep ART's canonical class-loader paths.
                (root / name).mkdir(mode=0o755)
            else:
                (root / name).symlink_to(target)
        shutil.copyfile(environ_rc, root / "init.environ.rc")
        shutil.copyfile(INPUT / "init.rc", root / "init.t110-core.rc")
        if full:
            shutil.copyfile(INPUT / "logging-test-policy", root / "t110-preload-policy")
            shutil.copyfile(INPUT / "init.mrvl.rc", root / "init.mrvl.rc")
            (root / "ueventd.mrvl.rc").write_text(
                "/dev/galcore 0666 system graphics\n/dev/ion 0666 system graphics\n"
            )
            # Both filesystems are already mounted by stage.c. Vold still needs
            # the data entry to recognize the unencrypted ext4 layout.
            (root / "fstab.mrvl").write_text(
                "/dev/block/loop0 /system ext4 ro wait\n"
                "/dev/block/mmcblk0p16 /data ext4 nosuid,nodev,noatime wait\n"
            )
            (root / "lib/modules").mkdir(parents=True)
            shutil.copyfile(module, root / "lib/modules/galcore.ko")
        shutil.copyfile(PROJECT / "work/native-ramdisk/cgroups.json", root / "t110-cgroups.json")
        props = root / "second_stage_resources/system/etc/ramdisk/build.prop"
        props.write_text(
            ("" if full else "ro.boot.init_rc=/init.t110-core.rc\n")
            + "ro.config.per_app_memcg=false\n"
            + ("ro.config.low_ram=true\nro.lmk.use_psi=false\nro.lmk.use_minfree_levels=true\n" if full else "")
            +
            f"ro.boot.t110_usb={int(not qemu)}\n"
        )
        gcc = ["arm-linux-gnueabi-gcc", "-static", "-O2", "-march=armv7-a",
               "-std=gnu11", "-Wall", "-Wextra", "-Werror"]
        if qemu:
            gcc.append("-DT110_QEMU")
        if full:
            gcc.append("-DT110_FULL_BOOT")
        subprocess.run([*gcc, INPUT / "stage.c", "-o", root / "init"], check=True)
        names = b"\0".join(str(p.relative_to(root)).encode() for p in sorted(root.rglob("*")))
        archive = subprocess.run(
            ["cpio", "--quiet", "-o", "-0", "-H", "newc", "--owner=0:0", "--reproducible"],
            cwd=root, input=names + b"\0", capture_output=True, check=True,
        ).stdout
        return gzip.compress(archive, mtime=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("environ_rc", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--kernel", type=Path)
    parser.add_argument("--kernel-sha256")
    parser.add_argument("--module", type=Path)
    parser.add_argument("--module-sha256")
    args = parser.parse_args()
    if args.full and not all((args.kernel, args.kernel_sha256, args.module, args.module_sha256)):
        parser.error("full boot requires pinned kernel and module")
    replacement_kernel = args.kernel.read_bytes() if args.kernel else None
    if replacement_kernel is not None:
        assert sha256(replacement_kernel) == args.kernel_sha256
    if args.module:
        assert sha256(args.module.read_bytes()) == args.module_sha256
    rd = ramdisk(args.environ_rc, qemu=False, full=args.full, module=args.module)
    qemu_rd = ramdisk(args.environ_rc, qemu=True, full=args.full, module=args.module)
    boot = boot_image(rd, replacement_kernel, fatal_recovery=args.full)
    full = boot.ljust(BOOT_BYTES, b"\0")
    args.destination.mkdir(parents=True, exist_ok=True)
    if any(args.destination.iterdir()):
        parser.error("destination must be empty")
    for name, content in {
        "ramdisk.cpio.gz": rd,
        "qemu-ramdisk.cpio.gz": qemu_rd,
        "boot.img": boot,
        "KERNEL.img": full,
    }.items():
        (args.destination / name).write_bytes(content)
    report = {
        "status": "PACKAGED",
        "kernel_sha256": args.kernel_sha256 or KERNEL_SHA256,
        "module_sha256": args.module_sha256,
        "ramdisk_sha256": sha256(rd),
        "qemu_ramdisk_sha256": sha256(qemu_rd),
        "boot_image_bytes": len(boot),
        "boot_partition_bytes": len(full),
        "full_boot_sha256": sha256(full),
        "full_boot_md5": hashlib.md5(full).hexdigest(),
        "system_mode": "read-only ext4 loop",
        "data_mode": "dedicated persistent directory" if args.full else "128 MiB tmpfs",
        "recovery_watchdog_seconds": 1200 if args.full else 150,
        "fatal_init_reboot_target": "recovery" if args.full else "platform default",
        "bootstrap_policy_sha256": sha256((INPUT / "logging-test-policy").read_bytes()) if args.full else None,
    }
    (args.destination / "provenance.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
