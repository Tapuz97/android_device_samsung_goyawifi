"""Apply evidence-backed Nougat settings, supplicant and permission fixes."""
from pathlib import Path

root = Path('/root/t110-lineage14/android')
def replace(path, old, new):
    p = root / path
    s = p.read_text()
    if new in s:
        return
    assert s.count(old) == 1, path
    p.write_text(s.replace(old, new))

replace('system/vold/cryptfs.c',
    '    return fs_mgr_is_convertible_to_fbe(rec) ? 1 : 0;',
    '    // A bootstrap-mounted /data may have no fstab record. It cannot be\n'
    '    // converted through fs_mgr; answer the capability query safely.\n'
    '    return rec && fs_mgr_is_convertible_to_fbe(rec) ? 1 : 0;')

replace('device/samsung/goyawifi/rootdir/init.mrvl.rc',
    '-c/data/misc/wifi/wpa_supplicant.conf -O/data/misc/wifi/sockets',
    '-c/data/misc/wifi/wpa_supplicant.conf -O/data/misc/wifi/sockets -g@android:wpa_wlan0')

replace('device/samsung/goyawifi/device.mk',
    '    frameworks/native/data/etc/android.hardware.wifi.xml:system/etc/permissions/android.hardware.wifi.xml \\\n',
    '    frameworks/native/data/etc/android.hardware.wifi.xml:system/etc/permissions/android.hardware.wifi.xml \\\n'
    '    frameworks/native/data/etc/android.hardware.usb.accessory.xml:system/etc/permissions/android.hardware.usb.accessory.xml \\\n')

replace('device/samsung/goyawifi/device.mk',
    '    frameworks/native/data/etc/android.hardware.bluetooth.xml:system/etc/permissions/android.hardware.bluetooth.xml \\\n',
    '    frameworks/native/data/etc/android.hardware.bluetooth.xml:system/etc/permissions/android.hardware.bluetooth.xml \\\n'
    '    frameworks/native/data/etc/android.hardware.bluetooth_le.xml:system/etc/permissions/android.hardware.bluetooth_le.xml \\\n')

replace('packages/apps/Camera2/src/com/android/camera/CameraActivity.java',
    '        if ((checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED &&',
    '        if ((!isKeyguardLocked() &&\n'
    '                checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED &&')

replace('packages/apps/Camera2/src/com/android/camera/PermissionsActivity.java',
    '                buildPermissionsRequest();\n            } else {',
    '                buildPermissionsRequest();\n'
    '            } else if (mFlagHasCameraPermission && mFlagHasMicrophonePermission\n'
    '                    && mFlagHasStoragePermission) {\n'
    '                // Location is optional, including when its prompt cannot be\n'
    '                // shown from the lock screen or was already declined.\n'
    '                handlePermissionsSuccess();\n'
    '            } else {')

replace('packages/apps/Camera2/src/com/android/camera/PermissionsActivity.java',
    '        mNumPermissionsToRequest = 0;\n        checkPermissions();',
    '        mNumPermissionsToRequest = 0;\n'
    '        mShouldRequestCameraPermission = false;\n'
    '        mShouldRequestMicrophonePermission = false;\n'
    '        mShouldRequestStoragePermission = false;\n'
    '        mShouldRequestLocationPermission = false;\n'
    '        mFlagHasCameraPermission = false;\n'
    '        mFlagHasMicrophonePermission = false;\n'
    '        mFlagHasStoragePermission = false;\n'
    '        checkPermissions();')
print('Applied Settings capability guard, global Wi-Fi socket and optional-location fixes.')
