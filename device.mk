LOCAL_PATH := device/samsung/goyawifi
DEVICE_PACKAGE_OVERLAYS += $(LOCAL_PATH)/overlay
PRODUCT_PACKAGES += lights.mrvl t110_radio_init t110_bt_init libbt-vendor t110_stage
PRODUCT_PACKAGES += wpa_supplicant hostapd libwpa_client audio.r_submix.default
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/rootdir/init.mrvl.rc:root/init.mrvl.rc \
    $(LOCAL_PATH)/rootdir/ueventd.mrvl.rc:root/ueventd.mrvl.rc \
    $(LOCAL_PATH)/configs/media_profiles.xml:system/etc/media_profiles.xml \
    $(LOCAL_PATH)/keylayout/gpio-keys.kl:system/usr/keylayout/gpio-keys.kl \
    $(LOCAL_PATH)/keylayout/sec_touchscreen.kl:system/usr/keylayout/sec_touchscreen.kl \
    frameworks/native/data/etc/android.hardware.touchscreen.multitouch.jazzhand.xml:system/etc/permissions/android.hardware.touchscreen.multitouch.jazzhand.xml \
    frameworks/native/data/etc/android.hardware.wifi.xml:system/etc/permissions/android.hardware.wifi.xml \
    frameworks/native/data/etc/android.hardware.usb.accessory.xml:system/etc/permissions/android.hardware.usb.accessory.xml \
    frameworks/native/data/etc/android.hardware.bluetooth.xml:system/etc/permissions/android.hardware.bluetooth.xml \
    frameworks/native/data/etc/android.hardware.bluetooth_le.xml:system/etc/permissions/android.hardware.bluetooth_le.xml \
    frameworks/native/data/etc/android.hardware.camera.xml:system/etc/permissions/android.hardware.camera.xml \
    frameworks/native/data/etc/android.software.app_widgets.xml:system/etc/permissions/android.software.app_widgets.xml \
    external/wpa_supplicant_8/wpa_supplicant/wpa_supplicant_template.conf:system/etc/wifi/wpa_supplicant.conf
$(call inherit-product-if-exists, device/samsung/goyawifi/vendor-blobs.mk)

PRODUCT_COPY_FILES += $(LOCAL_PATH)/rootdir/fstab.mrvl:root/fstab.mrvl $(LOCAL_PATH)/rootdir/fstab.t110.zram:root/fstab.t110.zram

PRODUCT_PACKAGES += libEGL libGLESv1_CM libGLESv2 libhardware_legacy libstdc++ libaudioutils libeffects libcamera_client libexpat libmedia

# API2.0 primary HAL uses Nougat profiles, with original hardware calibration.
PRODUCT_PACKAGES += audio.a2dp.default audio.usb.default
PRODUCT_COPY_FILES += $(LOCAL_PATH)/configs/audio_policy.conf:system/etc/audio_policy.conf
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_basic_element.xml:system/etc/audio_basic_element.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_coeff_config.xml:system/etc/audio_coeff_config.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_gain_config.xml:system/etc/audio_gain_config.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_path_config.xml:system/etc/audio_path_config.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_swvol_calibration_def.xml:system/etc/audio_swvol_calibration_def.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_swvol_config.xml:system/etc/audio_swvol_config.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_swvol_element.xml:system/etc/audio_swvol_element.xml

# Use the Nougat XML/ICU platform pair, not an old ICU48 vendor shadow.
PRODUCT_PACKAGES += libxml2

# Load the matched GPU module after the system loop is mounted; keep ramdisk small.
PRODUCT_COPY_FILES += $(LOCAL_PATH)/prebuilt/galcore.ko:system/vendor/lib/modules/galcore.ko
