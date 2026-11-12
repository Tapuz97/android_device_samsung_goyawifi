"""Derive the guarded paired delta installer, with an explicit old/new identity map."""
from pathlib import Path
p=Path(__file__).resolve().parents[1];source=(p/'scripts/install_bt_sd_v37.py').read_text();dest=p/'scripts/install_bt_v38.py';assert not dest.exists()
replacements={
 'v37-installation.json':'v38-installation.json',
 'lineage20-rom-v37-gapps':'lineage20-rom-v38-gapps',
 'lineage20-rom-v36-gapps':'lineage20-rom-v37-gapps',
 'android13-boot-v43':'android13-boot-v45',
 'android13-boot-v42':'android13-boot-v44',
 '8b5dc0d14169d5cb6f898d2f0e978242ace8aaef621a90ac47515939c887c0ab':'37c8eb8b95c8da19e5187ffffa9bde03aa0e17cf53680b819a230007bf554e77',
 "boot_meta['kernel_unchanged_from_boot42']":"boot_meta['kernel_unchanged_from_boot44']",
 'controller-probe-legacy.json':'boot44-installation.json',
 't110-v37-bt-sd-delta':'t110-v38-bt-startup-delta',
 'boot43.img':'boot45.img',
 'boot42-rollback.img':'boot44-rollback.img',
 'V37_BOOT43_VERIFIED_BOOTING':'V38_BOOT45_VERIFIED_BOOTING',
 'RESTORING_V36':'RESTORING_V37',
 "reverse_delta_retained=True":"reverse_delta_retained=True",
}
for before,after in replacements.items():
 if before==after:continue
 assert before in source,before
 source=source.replace(before,after)
assert 'boot43.img' not in source and 'boot42-rollback.img' not in source and 'controller-probe-legacy.json' not in source
source=source.replace('Install the verified BT/SD delta and matching policy boot','Install the native Bluetooth startup delta and matching platform-trigger boot')
dest.write_text(source);print('V38_PAIRED_INSTALLER_DERIVED_CHECK_EXACT_DIFF_BEFORE_RUNNING')
