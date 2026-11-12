# Native Android 13 userspace bootstrap, not a flashable ROM product yet.
TARGET_ARCH := arm
TARGET_ARCH_VARIANT := armv7-a-neon
TARGET_CPU_VARIANT := cortex-a9
TARGET_CPU_ABI := armeabi-v7a
TARGET_CPU_ABI2 := armeabi
TARGET_BOARD_PLATFORM := mrvl
TARGET_BOOTLOADER_BOARD_NAME := PXA988
TARGET_USES_64_BIT_BINDER := false
TARGET_NO_BOOTLOADER := true
TARGET_NO_KERNEL := true
TARGET_NO_RECOVERY := true
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 1594884096
BOARD_USERDATAIMAGE_PARTITION_SIZE := 5509218304
BOARD_FLASH_BLOCK_SIZE := 131072
TARGET_LD_SHIM_LIBS := /vendor/lib/hw/gralloc.mrvl.so|libt110_gralloc_binder_compat.so
BOARD_VENDOR_SEPOLICY_DIRS += device/samsung/t110_bringup/sepolicy
# Linux3.4 still checks file:swapon. Keep the legacy permission device-specific.
BOARD_SEPOLICY_M4DEFS += t110_legacy_swapon=true
DEVICE_MANIFEST_FILE := device/samsung/t110_bringup/graphics-manifest.xml
DEVICE_MANIFEST_FILE += device/samsung/t110_bringup/bluetooth/manifest.xml
TARGET_USERIMAGES_USE_EXT4 := true
# eng normally precompiles only the boot classpath and system-server jars.
# Include apps too, particularly PermissionController and the initial UI.
WITH_DEXPREOPT_BOOT_IMG_AND_SYSTEM_SERVER_ONLY := false
# Use Android 13's standard AIDL supplicant with the cfg80211 Marvell driver.
WPA_SUPPLICANT_VERSION := VER_0_8_X
BOARD_WPA_SUPPLICANT_DRIVER := NL80211
WIFI_HIDL_UNIFIED_SUPPLICANT_SERVICE_RC_ENTRY := true
