from pathlib import Path
import subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
repo=Path('/root/t110-build/lineage20/packages/apps/SetupWizard')
manifest=repo/'AndroidManifest.xml';s=manifest.read_text()
assert 'android:hardwareAccelerated=' not in s
s=s.replace('<application android:label=', '<application android:hardwareAccelerated="@bool/config_setupHardwareAccelerated"\n                 android:label=')
manifest.write_text(s)
# Use an existing resource file so the configuration is also documented with
# the app defaults. The product overlay disables it only for this legacy GPU.
config=repo/'res/values/config.xml';s=config.read_text()
assert 'config_setupHardwareAccelerated' not in s
s=s.replace('</resources>','    <!-- Device overlays may use CPU Canvas for unsupported legacy GPUs. -->\n    <bool name="config_setupHardwareAccelerated">true</bool>\n</resources>')
config.write_text(s)
patch=subprocess.check_output(['git','diff','--','AndroidManifest.xml','res/values/config.xml'],cwd=repo)
(p/'patches/0057-setupwizard-configurable-canvas-rendering.patch').write_bytes(patch)
overlay=p/'work/device/samsung/t110_bringup/overlay/packages/apps/SetupWizard/res/values/config.xml'
overlay.parent.mkdir(parents=True,exist_ok=True)
overlay.write_text('''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <!-- The T110 stock GLES driver corrupts the portrait setup scene. -->
    <bool name="config_setupHardwareAccelerated">false</bool>
</resources>
''')
product=p/'work/device/samsung/t110_bringup/t110_system.mk';s=product.read_text()
assert 'DEVICE_PACKAGE_OVERLAYS' not in s
s+='\n# Legacy GPU compatibility for the setup activity; other applications retain GPU drawing.\nDEVICE_PACKAGE_OVERLAYS += device/samsung/t110_bringup/overlay\n'
product.write_text(s)
build=p/'scripts/build_system_image.sh';s=build.read_text()
needle="'external/libfuse:0051-libfuse-unsigned-passthrough-mask.patch'"
assert needle in s
s=s.replace(needle,needle+" 'packages/apps/SetupWizard:0057-setupwizard-configurable-canvas-rendering.patch'")
build.write_text(s)
print('DEVICE_ONLY_SETUP_CANVAS_FALLBACK_PREPARED')
