"""Test staged Android; failed full-ROM trials stay in recovery with logs captured."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


PROJECT = Path(__file__).resolve().parents[1]
ADB = Path(os.environ["LOCALAPPDATA"]) / "Android/Sdk/platform-tools/adb.exe"
SERIAL = "T110_ADB_SERIAL"
STOCK = PROJECT / "backups/20261104T201457Z/KERNEL.img"
STOCK_MD5 = "7847f1b7e68e49e9ca590e052f0f76c4"
OLD_TRIAL = PROJECT / "hardware-tests/20261105-140246-hwbinder"
OLD_TRIAL_MD5 = "1cbc47be853e2b5100d85be34ab73681"
REMOTE_IMAGE = "/tmp/t110-core-boot.img"
REMOTE_STOCK = "/tmp/t110-stock-boot.img"
RECOVERY_TEST = '[ "$(id -u)" = 0 ] && [ -x /sbin/recovery ] && echo T110_TWRP_READY'
STOCK_TEST = (
    '[ "$(getprop sys.boot_completed)" = 1 ] && '
    '[ "$(getprop ro.product.device)" = goyawifi ] && echo T110_STOCK_READY'
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--sha256", required=True, help="Verified candidate BOOT SHA-256")
    parser.add_argument("--egl-probe", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--system-md5")
    parser.add_argument("--from-recovery", action="store_true")
    parser.add_argument("--expected-boot-md5")
    parser.add_argument("--reuse-boot", action="store_true",
                        help="Verify and retain an already installed identical BOOT")
    parser.add_argument("--stability-seconds", type=int, default=0,
                        help="Observe the same system_server after boot_completed")
    args = parser.parse_args()
    if args.full and not (args.system_md5 and re.fullmatch(r"[0-9a-f]{32}", args.system_md5)):
        parser.error("--full requires the verified staged system MD5")
    if args.from_recovery and not (args.expected_boot_md5 and re.fullmatch(r"[0-9a-f]{32}", args.expected_boot_md5)):
        parser.error("--from-recovery requires the previously verified BOOT MD5")
    if not 0 <= args.stability_seconds <= 600:
        parser.error("--stability-seconds must be between 0 and 600")
    payload = args.artifact / "KERNEL.img"
    metadata = json.loads((args.artifact / "provenance.json").read_text())
    assert payload.stat().st_size == STOCK.stat().st_size == 16777216
    contents = payload.read_bytes()
    assert hashlib.sha256(contents).hexdigest() == metadata["full_boot_sha256"] == args.sha256
    image_md5 = hashlib.md5(contents).hexdigest()
    assert image_md5 == metadata["full_boot_md5"]
    if args.reuse_boot and not (args.full and args.from_recovery and
                               args.expected_boot_md5 == image_md5):
        parser.error("--reuse-boot requires a full recovery boot with identical installed BOOT")
    assert hashlib.md5(STOCK.read_bytes()).hexdigest() == STOCK_MD5
    trial = PROJECT / "hardware-tests" / time.strftime("%Y%m%d-%H%M%S-core")
    trial.mkdir()
    print(trial, flush=True)

    def adb(*command, timeout=30, check=True):
        result = subprocess.run(
            [str(ADB), "-s", SERIAL, *map(str, command)], capture_output=True,
            text=True, errors="replace", timeout=timeout,
        )
        output = result.stdout + result.stderr
        with (trial / "adb.log").open("a", encoding="utf-8") as log:
            log.write(f"{command!r} => {result.returncode}\n{output}\n")
        if check and result.returncode:
            raise RuntimeError(output)
        return output

    def wait(command, marker, seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                if marker in adb("shell", command, timeout=6, check=False):
                    return
            except subprocess.TimeoutExpired:
                pass
            time.sleep(2)
        raise TimeoutError(marker)

    def record(name, command):
        try:
            output = adb("shell", command, timeout=15, check=False)
        except subprocess.TimeoutExpired as error:
            output = "CAPTURE_TIMEOUT\n" + str(error.output or "")
        (trial / name).write_text(output, encoding="utf-8")
        return output

    def write_script(name, boot_md5=image_md5):
        script = (OLD_TRIAL / f"{name}.sh").read_text()
        script = script.replace(OLD_TRIAL_MD5, boot_md5).replace(
            "/tmp/t110-android13-v5.img", REMOTE_IMAGE
        )
        if name == "flash" and args.from_recovery:
            script = script.replace(
                f"/dev/block/mmcblk0p10 | cut -d' ' -f1) = {STOCK_MD5}",
                f"/dev/block/mmcblk0p10 | cut -d' ' -f1) = {args.expected_boot_md5}",
            )
        path = trial / f"{name}.sh"
        path.write_bytes(script.encode())
        remote = "/tmp/" + path.name
        adb("push", path, remote)
        return remote

    def try_egl():
        bundle = PROJECT / "artifacts/egl-probe"
        graphics = PROJECT / "artifacts/framebuffer-probe"
        module = PROJECT / "artifacts/kernel-native-init-ffs/modules/galcore.ko"
        module_pin = json.loads((module.parent / "provenance.json").read_text())
        graphics_pins = json.loads((graphics / "provenance.json").read_text())
        assert module_pin["paired_kernel_sha256"] == metadata["kernel_sha256"]
        assert hashlib.sha256(module.read_bytes()).hexdigest() == module_pin["sha256"]
        directory = "/data/local/tmp/t110-egl"
        adb(
            "shell",
            "test -f /init.t110-core.rc && "
            "ln -s /init.t110-core.rc /t110-native-diagnostic && "
            f"mkdir -p /tmp {directory}",
        )
        for line in (bundle / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split()
            assert re.fullmatch(r"[a-zA-Z0-9_.+]+", name)
            file = bundle / name
            assert hashlib.sha256(file.read_bytes()).hexdigest() == digest
            adb("push", file, f"{directory}/{name}")
        adb("push", bundle / "SHA256SUMS", f"{directory}/SHA256SUMS")
        for name in ("t110_load_galcore", "t110_galcore_query"):
            file = graphics / name
            assert hashlib.sha256(file.read_bytes()).hexdigest() == graphics_pins["artifacts"][name]
            adb("push", file, f"/tmp/{name}")
        adb("push", module, "/tmp/t110-galcore.ko")
        gpu = record(
            "galcore.txt",
            "chmod 0755 /tmp/t110_load_galcore /tmp/t110_galcore_query && "
            '[ "$(sha256sum /tmp/t110-galcore.ko | cut -d\' \' -f1)" = '
            f'{module_pin["sha256"]} ] && /tmp/t110_load_galcore && '
            'sleep 1 && /tmp/t110_galcore_query',
        )
        print(gpu, flush=True)
        if "GALCORE_INIT_MODULE_PASS" not in gpu or "model=0x1000" not in gpu:
            raise RuntimeError("Vivante module or identity check failed")
        egl = adb(
            "shell", "-tt",
            f"cd {directory} && sha256sum -c SHA256SUMS && chmod 0755 t110_egl_probe || exit 1; "
            f"export LD_LIBRARY_PATH={directory}; "
            "./t110_egl_probe default; ./t110_egl_probe 22",
            timeout=18, check=False,
        )
        (trial / "egl-probe.txt").write_text(egl, encoding="utf-8")
        print(egl, flush=True)

    staged = "/data/local/tmp/t110-rom-system.raw" if args.full else "/data/local/tmp/t110-stage-system.raw"
    keep_running = False
    returned_to_recovery = False
    if not args.from_recovery:
        wait(STOCK_TEST, "T110_STOCK_READY", 15)
        assert "1594884096" in adb("shell", "ls -l " + staged)
        adb("reboot", "recovery")
    wait(RECOVERY_TEST, "T110_TWRP_READY", 75)
    if args.full:
        assert adb("shell", "md5sum " + staged, timeout=150).split()[0] == args.system_md5
    if args.reuse_boot:
        verify_script = f'''set -e
[ "$(id -u)" = 0 ]
[ -x /sbin/recovery ]
[ "$(cat /sys/class/block/mmcblk0/device/cid)" = 1101003030384745T110_ADB_SERIAL ]
[ "$(cat /sys/class/block/mmcblk0p10/size)" = 32768 ]
[ "$(cat /sys/class/block/mmcblk0p10/start)" = 163840 ]
[ "$(md5sum /dev/block/mmcblk0p10 | cut -d' ' -f1)" = {image_md5} ]
[ "$(md5sum /dev/block/mmcblk0p9 | cut -d' ' -f1)" = cd9793e1ee8f284c9056b225885b5b1a ]
echo EXISTING_BOOT_AND_RECOVERY_VERIFIED
'''
        assert "EXISTING_BOOT_AND_RECOVERY_VERIFIED" in adb("shell", verify_script)
    else:
        adb("push", payload, REMOTE_IMAGE)
        adb("push", STOCK, REMOTE_STOCK)
        flash = write_script("flash")
    try:
        if not args.reuse_boot:
            assert "FLASH_AND_RECOVERY_VERIFIED" in adb("shell", "/sbin/sh " + flash, timeout=60)
        print("ROM, matching BOOT and recovery verified. Starting LineageOS.", flush=True)
        adb("shell", "/sbin/reboot recovery_done", check=False)
        wait(
            '[ -f /init.t110-core.rc ] && [ -x /system/bin/servicemanager ] && echo T110_CORE_ADB',
            "T110_CORE_ADB", 180 if args.full else 95,
        )
        print("LineageOS core ADB is online.", flush=True)
        record("core-state.txt", "id; getenforce; getprop; cat /proc/mounts; ps -A")
        record("service-list.txt", "service list; lshal")
        record("kernel-before-graphics.txt", "dmesg")
        if args.full:
            # One uninterrupted full boot, bounded by the kernel-stage watchdog.
            uptime = float(adb("shell", "cat /proc/uptime").split()[0])
            deadline = time.monotonic() + max(0, 1120 - uptime)
            sample = 0
            observed_system_server = None
            completed_at = None
            while time.monotonic() < deadline:
                state = record(f"full-state-{sample}.txt", "getprop sys.boot_completed; getprop init.svc.zygote; getprop init.svc.surfaceflinger; getprop init.svc.bootanim; ps -A")
                server_pids = [line.split()[1] for line in state.splitlines()
                               if len(line.split()) > 2 and line.split()[-1] == "system_server"]
                if args.stability_seconds and server_pids:
                    current_server = server_pids[0]
                    if observed_system_server and current_server != observed_system_server:
                        (trial / "stability-failed.json").write_text(json.dumps({
                            "reason": "system_server restarted within the same boot",
                            "original_pid": observed_system_server,
                            "replacement_pid": current_server,
                            "boot_completed_observed": completed_at is not None,
                        }, indent=2) + "\n")
                        print("SYSTEM_SERVER_RESTART_DETECTED: saving this boot and returning to recovery.", flush=True)
                        break
                    observed_system_server = current_server
                if sample % 3 == 0:
                    boot_log = record(f"full-logcat-{sample}.txt", "logcat -b all -d -t 2400 'snet_event_log:S' '*:V'")
                    record(f"full-graphics-{sample}.txt", "logcat -b main -b system -b crash -d -s SurfaceFlinger RenderEngine Gralloc2 GraphicBufferAllocator v_gralloc AudioFlinger AndroidRuntime DEBUG")
                    if args.stability_seconds and "*** FATAL EXCEPTION IN SYSTEM PROCESS:" in boot_log:
                        (trial / "stability-failed.json").write_text(json.dumps({
                            "reason": "Fatal system_server exception captured",
                            "original_pid": observed_system_server,
                            "boot_completed_observed": completed_at is not None,
                            "log": f"full-logcat-{sample}.txt",
                        }, indent=2) + "\n")
                        print("SYSTEM_SERVER_FATAL_CAPTURED: returning to recovery.", flush=True)
                        break
                if state.splitlines() and state.splitlines()[0].strip() == "1":
                    if completed_at is None:
                        completed_at = time.monotonic()
                        record("boot-completed.txt", "getprop; dumpsys activity activities; dumpsys SurfaceFlinger")
                        print("ANDROID_BOOT_COMPLETED: observing startup stability.", flush=True)
                    if server_pids and time.monotonic() - completed_at >= args.stability_seconds:
                        keep_running = True
                        (trial / "stability-observation.json").write_text(json.dumps({
                            "system_server_pid": observed_system_server,
                            "seconds_after_boot_completed": time.monotonic() - completed_at,
                            "restart_observed": False,
                            "usable_ui_validated": False,
                        }, indent=2) + "\n")
                        print("ANDROID_STABILITY_WINDOW_COMPLETE: leaving ROM running for UI verification.", flush=True)
                        break
                try:
                    if "T110_TWRP_READY" in adb("shell", RECOVERY_TEST, check=False, timeout=8):
                        returned_to_recovery = True
                        break
                except subprocess.TimeoutExpired:
                    pass  # Transient USB loss is not a second boot attempt.
                sample += 1
                time.sleep(min(25, max(0, deadline - time.monotonic())))
            record("full-dmesg.txt", "dmesg")
            if not keep_running and not returned_to_recovery:
                try:
                    adb("reboot", "recovery", check=False)
                except subprocess.TimeoutExpired:
                    # USB can disappear before adbd acknowledges the request.
                    # The finally block verifies recovery and captures evidence.
                    print("Reboot acknowledgement timed out; checking actual recovery state.", flush=True)
        elif args.egl_probe:
            try_egl()
            record("egl-logcat.txt", "logcat -d -t 350")
        else:
            adb("shell", "setprop ctl.start surfaceflinger", check=False)
            time.sleep(8)
            record("surfaceflinger.txt", "getprop init.svc.surfaceflinger; service list; logcat -d -t 350")
        record("kernel-after-graphics.txt", "dmesg")
    finally:
        if not keep_running:
            print("Waiting for recovery; the full-ROM trial will remain there.", flush=True)
            try:
                wait(RECOVERY_TEST, "T110_TWRP_READY", 660 if args.full else 175)
            except TimeoutError:
                (trial / "result.json").write_text(json.dumps({
                    "boot_completed": False,
                    "tablet_state": "No recovery ADB; physical state unconfirmed",
                    "stock_rollback_performed": False,
                    "candidate_boot_md5": image_md5,
                    "persistent_logs_retrieved": False,
                }, indent=2) + "\n")
                raise
            record("last-kmsg.txt", "cat /proc/last_kmsg")
            if args.full:
                names = re.findall(r"boot-[0-9]{4}", adb("shell", "ls /data/local/tmp/t110-bootlogs"))
                latest = max(names) if names else ""
                if re.fullmatch(r"boot-[0-9]{4}", latest):
                    adb("pull", "/data/local/tmp/t110-bootlogs/" + latest, trial / "persistent-bootlogs", timeout=90, check=False)
                adb("pull", "/data/local/tmp/t110-rom-data/tombstones", trial / "tombstones", timeout=90, check=False)
                adb("pull", "/data/local/tmp/t110-rom-data/local/tmp", trial / "android-logs", timeout=90, check=False)
                record("recovery-state.txt", "md5sum /dev/block/mmcblk0p10 /dev/block/mmcblk0p9; cat /proc/mounts")
                snapshots = [p for p in (trial / "persistent-bootlogs").rglob("kernel-*.txt") if p.stat().st_size]
                (trial / "result.json").write_text(json.dumps({
                    "boot_completed": False, "tablet_state": "TWRP",
                    "stock_rollback_performed": False,
                    "persistent_kernel_snapshots": len(snapshots),
                }, indent=2) + "\n")
                print(f"RECOVERY_HELD: {len(snapshots)} persistent kernel snapshots saved; no stock rollback performed.", flush=True)
            else:
                installed = adb("shell", "md5sum /dev/block/mmcblk0p10").split()[0]
                assert re.fullmatch(r"[0-9a-f]{32}", installed)
                if installed != STOCK_MD5:
                    adb("push", STOCK, REMOTE_STOCK)
                    rollback = write_script("rollback", installed)
                    assert "STOCK_BOOT_AND_RECOVERY_VERIFIED" in adb("shell", "/sbin/sh " + rollback, timeout=60)
                adb("shell", "/sbin/reboot recovery_done", check=False)
                wait(STOCK_TEST, "T110_STOCK_READY", 120)
                record("stock-return.txt", "getprop ro.build.version.release; getprop sys.boot_completed")
                print("Stock Android boot verified.", flush=True)



if __name__ == "__main__":
    main()
