"""Static source audit only. Exit 2 means unresolved build/boot blockers."""
from pathlib import Path
import json
import hashlib
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DEVICE = ROOT / "work/device/samsung/goyawifi"

def read(path):
    return path.read_text(encoding="utf-8")

def inspect():
    manifest = read(ROOT / "sources/los13-manifest/roomservice.xml")
    board = read(DEVICE / "BoardConfig.mk")
    product = read(DEVICE / "device_goyawifi.mk")
    config = read(ROOT / "evidence/kernel-config.txt")
    fixed = {
        "product_registered": "PRODUCT_MAKEFILES := $(LOCAL_DIR)/lineage.mk" in read(DEVICE / "AndroidProducts.mk"),
        "base_product_inherited": "product/full_base.mk" in read(DEVICE / "lineage.mk"),
        "kernel_path_matches_manifest": "kernel/samsung/goya\n" in board and 'path="kernel/samsung/goya"' in manifest,
        "android_defconfig_selected": "cyanogenmod_goyawifi_defconfig" in board,
        "vendor_inheritance_matches_manifest": "vendor/samsung/goya/goya-vendor.mk" in product,
    }
    blockers = []
    original_kernel_findings = []
    for symbol in ["CONFIG_SECURITY", "CONFIG_CGROUPS", "CONFIG_EXT4_FS_SECURITY"]:
        if f"# {symbol} is not set" in config:
            original_kernel_findings.append(f"Original defconfig disables {symbol}")
    if "#define NR_SECCOMP_MODES 1" in read(ROOT / "evidence/kernel-seccomp.txt"):
        original_kernel_findings.append("Original kernel seccomp is strict-mode only")
    for match in re.finditer(r"PRODUCT_PACKAGES\s*\+=\s*((?:[^\n]*\\\n)*[^\n]*)", product):
        paths = re.findall(r"\$\(LOCAL_PATH\)/[^\s\\]+", match.group(1))
        if paths:
            blockers.append("File paths used as module names: " + ", ".join(paths))
    if 'remove-project name="LineageOS/android_hardware_libhardware"' in manifest:
        blockers.append("Original manifest replaces Android 13 hardware/libhardware with a legacy fork")
    if "systemights.pxa988" in product:
        blockers.append("Media configuration has malformed destination systemights.pxa988/etc")
    if "$(LOCAL_PATH)/rootdir/init.board.rc" in product and not (DEVICE / "rootdir/init.board.rc").exists():
        blockers.append("Referenced init.board.rc does not exist")
    candidate = ROOT / "artifacts/kernel-binder-modern"
    provenance = json.loads(read(candidate / "build-provenance.json"))
    validation = json.loads(read(ROOT / "artifacts/qemu-binder-modern/validation.json"))
    candidate_config = read(candidate / "kernel.config")
    required = ["CONFIG_SECURITY", "CONFIG_SECURITY_SELINUX", "CONFIG_CGROUPS",
                "CONFIG_EXT4_FS_SECURITY", "CONFIG_SECCOMP", "CONFIG_SECCOMP_FILTER", "CONFIG_ANDROID_BINDER_IPC", "CONFIG_ANDROID_BINDER_IPC_32BIT"]
    kernel_checks = {symbol: f"{symbol}=y" in candidate_config for symbol in required}
    kernel_checks["binder_device_contexts"] = 'CONFIG_ANDROID_BINDER_DEVICES="binder,hwbinder,vndbinder"' in candidate_config
    kernel_checks["unsupported_user_namespaces_disabled"] = '# CONFIG_USER_NS is not set' in candidate_config
    kernel_checks["config_hash_matches_provenance"] = hashlib.sha256((candidate / "kernel.config").read_bytes()).hexdigest() == provenance["config_sha256"]
    kernel_checks["patch_hashes_match_provenance"] = all(hashlib.sha256((ROOT / entry["file"]).read_bytes()).hexdigest() == entry["sha256"] for entry in provenance["patches"])
    kernel_checks["zImage_hash_matches_provenance"] = hashlib.sha256((candidate / "zImage").read_bytes()).hexdigest() == provenance["sha256"]
    kernel_checks["qemu_validation_artifacts_match_hashes"] = all(
        hashlib.sha256((ROOT / "artifacts/qemu-binder-modern" / name).read_bytes()).hexdigest() == digest
        for name, digest in validation["files"].items())
    if not all(kernel_checks.values()):
        blockers.append("Candidate artifact/config verification failed")
    blockers.extend([
        "Patched kernel/config remain separate from the Android product and original manifest; integration is pending",
        "Full Android Binder service stack remains unvalidated. Android 13 libbinder and HIDL Binder two-process hardware roundtrips passed",
        "Android 13 normal-boot services, production policy and graphics/HAL integration remain unvalidated; RAM-only init/USB diagnostic passed",
        "Full source sync is complete; no complete bootable OS image exists; consult BUILD-WORKSPACE.json for live build/storage state",
    ])
    storage_record = ROOT / "storage-diagnostics/LATEST-RESULT.json"
    storage_verification = json.loads(read(storage_record)) if storage_record.exists() else None
    hardware_status = "No completed storage repair record; consult hardware diagnostics before testing"
    if storage_verification and storage_verification.get("status") == "REPAIRED_AND_VERIFIED":
        hardware_status = "Recorded SYSTEM repair, full main-area read scan and stock boot/file checks passed; controlled hardware testing may resume; monitor for recurrence"
    hardware_record = ROOT / "hardware-tests/LATEST-RESULT.json"
    hardware_verification = json.loads(read(hardware_record)) if hardware_record.exists() else None
    if hardware_verification and hardware_verification.get("kernel_sha256") == provenance["sha256"]:
        hardware_status = "Patched kernel booted diagnostic userspace; 15 native checks and user display/touch confirmation passed. One MMC timeout recovered on retry; reliability remains open. Consult latest hardware record for current boot state."
    if hardware_verification and hardware_verification.get("status") == "ANDROID13_MINIMAL_INIT_ADB_HARDWARE_BOOT_PASSED":
        image = ROOT / hardware_verification['artifact'] / 'KERNEL.img'
        hardware_verification['saved_boot_hash_matches'] = hashlib.sha256(image.read_bytes()).hexdigest() == hardware_verification['full_boot_sha256']
        if not hardware_verification['saved_boot_hash_matches']:
            blockers.append('Saved modern native boot image hash mismatch')
        hardware_status = "Android 13 RAM-only init and root USB ADB passed on hardware, including Binder and USB transfer/reconnect. Engineering policy only. Stock Android restored; full graphical OS not booted."
    bionic_record = ROOT / "artifacts/android13-native/bionic-result.json"
    bionic_verification = json.loads(read(bionic_record)) if bionic_record.exists() else None
    if bionic_verification:
        binary = ROOT / "artifacts/android13-native/t110_bionic_probe"
        bionic_verification["saved_binary_hash_matches"] = (
            binary.exists() and hashlib.sha256(binary.read_bytes()).hexdigest() ==
            bionic_verification.get("probe_sha256"))
        if not bionic_verification["saved_binary_hash_matches"]:
            blockers.append("Saved Android 13 bionic probe hash mismatch")
    binder_record = ROOT / "artifacts/android13-native/binder-result.json"
    binder_verification = json.loads(read(binder_record)) if binder_record.exists() else None
    if binder_verification:
        bundle = ROOT / "artifacts/android13-native/t110-native-probes.tar"
        binder_verification["saved_bundle_hash_matches"] = (
            bundle.exists() and hashlib.sha256(bundle.read_bytes()).hexdigest() ==
            binder_verification.get("bundle_sha256"))
        if not binder_verification["saved_bundle_hash_matches"]:
            blockers.append("Saved Android 13 Binder probe bundle hash mismatch")
    return {"kind": "static-product-audit-with-compiled-kernel-evidence", "wiring_checks": fixed,
            "original_kernel_findings": original_kernel_findings,
            "separate_kernel_candidate": {"artifact": "artifacts/kernel-binder-modern/zImage", "checks": kernel_checks,
                "qemu_tests_passed": len(validation["tests"]), "build_time_status": provenance["status"],
                "hardware_verification": hardware_verification},
            "blockers": blockers, "bootability": "UNPROVEN",
            "hardware_status": hardware_status,
            "android13_native_bionic_verification": bionic_verification,
            "android13_native_binder_verification": binder_verification,
            "storage_verification": {"record": str(storage_record.relative_to(ROOT)),
                "status": storage_verification.get("status") if storage_verification else None,
                "scope": "Saved evidence only; this preflight does not probe live hardware health"},
            "android13_rom_artifact": None}

if __name__ == "__main__":
    result = inspect()
    output = json.dumps(result, indent=2)
    (ROOT / "preflight.json").write_text(output + "\n", encoding="utf-8")
    print(output)
    sys.exit(2 if result["blockers"] or not all(result["wiring_checks"].values()) else 0)
