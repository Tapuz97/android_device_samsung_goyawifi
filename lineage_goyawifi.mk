$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base.mk)
$(call inherit-product, vendor/cm/config/common_full_tablet_wifionly.mk)
$(call inherit-product, frameworks/native/build/tablet-7in-hdpi-1024-dalvik-heap.mk)
$(call inherit-product, device/samsung/goyawifi/device.mk)
PRODUCT_NAME := lineage_goyawifi
PRODUCT_DEVICE := goyawifi
PRODUCT_BRAND := samsung
PRODUCT_MODEL := SM-T110
PRODUCT_MANUFACTURER := samsung
PRODUCT_CHARACTERISTICS := tablet
TARGET_SCREEN_WIDTH := 600
TARGET_SCREEN_HEIGHT := 1024
PRODUCT_AAPT_CONFIG := normal large mdpi hdpi
PRODUCT_AAPT_PREF_CONFIG := mdpi
PRODUCT_PROPERTY_OVERRIDES += ro.sf.lcd_density=200 ro.sf.hwrotation=270 ro.opengles.version=131072
PRODUCT_PROPERTY_OVERRIDES += wifi.interface=wlan0 ro.zygote.disable_gl_preload=true
PRODUCT_PROPERTY_OVERRIDES += ro.t110.legacy_gpu=true
PRODUCT_PROPERTY_OVERRIDES += persist.sys.strictmode.disable=true
PRODUCT_DEFAULT_PROPERTY_OVERRIDES += ro.secure=1 ro.adb.secure=1 persist.sys.usb.config=adb
# Android7.1 JIT uses ashmem: retain normal runtime and GPU app rendering.
WITH_DEXPREOPT := true

PRODUCT_PROPERTY_OVERRIDES += ro.bt.bdaddr_path=/data/vendor/t110-bluetooth/controller_address

PRODUCT_PROPERTY_OVERRIDES += persist.sys.sdcardfs=force_off
