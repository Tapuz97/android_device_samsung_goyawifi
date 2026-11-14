from pathlib import Path
import json

root = Path('/root/t110-android13')
board = root / 'android/device/samsung/t110_bringup/BoardConfig.mk'
stage = Path('/root/t110-lineage14/reference/current-private/work/core-boot/stage.c')
text = board.read_text()
assert 'supported_image_size |= info.st_size == 2146435072;' in stage.read_text()
old = 'BOARD_SYSTEMIMAGE_PARTITION_SIZE := 1594884096'
new = '''# Read-only loop file on userdata, NOT the faulty physical SYSTEM partition.
# This exact 2047 MiB geometry is supported by the preserved full-boot stage
# and stays below the signed ARM32 off_t limit.
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 2146435072'''
if old in text:
    board.write_text(text.replace(old, new))
else:
    assert new in text, 'Unexpected existing image geometry'
Path('/root/t110-android13-audit/complete-image-geometry.json').write_text(json.dumps(
    dict(bytes=2146435072, block_size=4096, blocks=524032, backing='userdata read-only loop file',
         physical_system_write=False, boot_stage_size_supported=True, hardware_tested=False), indent=2) + '\n')
print('Prepared supported 2047 MiB loop-file geometry; current active build graph will pick this up on its next invocation.')
