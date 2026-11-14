from pathlib import Path
import json

device=Path('/root/t110-android13/android/device/samsung/t110_bringup')
uevent=device/'graphics/ueventd.t110.rc'
text='''# Exact GOYA nodes, matching the qualified14.1 GPU access contract.
# Android13's graphics subsystem creates the actual node under /dev/graphics.
/dev/graphics/galcore 0666 system graphics
/dev/galcore 0666 system graphics
/dev/ion 0666 system graphics
/dev/mbtchar* 0660 system bluetooth
'''
if not uevent.exists() or uevent.read_text()!=text:uevent.write_text(text)
mk=device/'graphics.mk';current=mk.read_text()
line='PRODUCT_COPY_FILES += device/samsung/t110_bringup/graphics/ueventd.t110.rc:$(TARGET_COPY_OUT_VENDOR)/etc/ueventd.rc'
if line not in current:mk.write_text(current+'\n# Canonical Android13 ueventd import; retain the legacy ramdisk rules too.\n'+line+'\n')
contexts=device/'sepolicy/file_contexts';current=contexts.read_text()
line='/dev/graphics/galcore u:object_r:gpu_device:s0'
if line not in current:contexts.write_text(current+'\n# Actual node, not graphics_device (ordinary apps are forbidden that type).\n'+line+'\n')
Path('/root/t110-android13-audit/gpu-node-carryover.json').write_text(json.dumps(dict(
    status='SOURCE_READY_REBUILD_AND_IMAGE_CHECK_PENDING',device_node='/dev/graphics/galcore',
    legacy_alias='/dev/galcore',label='gpu_device',dac='0666 system graphics',
    source='qualified14.1 exact-node rule; confirmed Android13 ueventd graphics dirname',
    broad_graphics_permission_added=False,hardware_tested=False),indent=2)+'\n')
print('Restored exact GPU node DAC/label in normal vendor ueventd; matching boot will provide the legacy alias.')
