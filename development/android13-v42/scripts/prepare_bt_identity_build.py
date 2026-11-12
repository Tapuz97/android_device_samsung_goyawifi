from pathlib import Path
p=Path(__file__).resolve().parents[1];source=(p/'scripts/build_bt_runpath.sh').read_text()
source=source.replace('bluetooth-runpath-','bluetooth-identity-mode-').replace('hal-runpath-build-log.txt','identity-build-log.txt').replace('m -j2 android.hardware.bluetooth@1.1-service','m -j2 t110_bt_init')
(p/'scripts/build_bt_identity_mode.sh').write_bytes(source.encode());print('IDENTITY_LOADER_BUILD_WRAPPER_READY')
