# SM-T110 only. Matched kernel/modules from the preserved BOOT48 checkpoint.
TARGET_ARCH := arm
TARGET_ARCH_VARIANT := armv7-a-neon
TARGET_CPU_VARIANT := cortex-a9
TARGET_CPU_ABI := armeabi-v7a
TARGET_CPU_ABI2 := armeabi
TARGET_CPU_SMP := true
TARGET_BOARD_PLATFORM := mrvl
TARGET_BOOTLOADER_BOARD_NAME := PXA988
TARGET_USES_64_BIT_BINDER := false
TARGET_NO_BOOTLOADER := true
TARGET_NO_RADIOIMAGE := true
TARGET_NO_RECOVERY := true
TARGET_PREBUILT_KERNEL := device/samsung/goyawifi/prebuilt/zImage
BOARD_KERNEL_BASE := 0x10000000
BOARD_KERNEL_PAGESIZE := 2048
BOARD_MKBOOTIMG_ARGS := --ramdisk_offset 0x01000000
BOARD_KERNEL_CMDLINE := androidboot.init_fatal_reboot_target=recovery androidboot.hardware=mrvl androidboot.selinux=permissive
TARGET_USERIMAGES_USE_EXT4 := true
BOARD_BOOTIMAGE_PARTITION_SIZE := 16777216
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 1594884096
BOARD_USERDATAIMAGE_PARTITION_SIZE := 5509218304
BOARD_FLASH_BLOCK_SIZE := 131072
BOARD_HAS_NO_MISC_PARTITION := true
TARGET_USES_HWC2 := false
TARGET_NEEDS_PLATFORM_TEXT_RELOCATIONS := true
USE_OPENGL_RENDERER := true
TARGET_RUNNING_WITHOUT_SYNC_FRAMEWORK := true
BOARD_EGL_CFG := device/samsung/goyawifi/configs/egl.cfg
NUM_FRAMEBUFFER_SURFACE_BUFFERS := 3
WPA_SUPPLICANT_VERSION := VER_0_8_X
BOARD_WPA_SUPPLICANT_DRIVER := NL80211
BOARD_HOSTAPD_DRIVER := NL80211
BOARD_WLAN_DEVICE := mrvl
BOARD_HAVE_BLUETOOTH := true
BOARD_BLUETOOTH_BDROID_BUILDCFG_INCLUDE_DIR := device/samsung/goyawifi/bluetooth
BOARD_SEPOLICY_DIRS += device/samsung/goyawifi/sepolicy

TARGET_SPECIFIC_HEADER_PATH := device/samsung/goyawifi/include

# combo/select.mk resets TARGET_GLOBAL_CFLAGS; evaluate only in the target combo.
BOARD_GLOBAL_CFLAGS += $(if $(filter TARGET_,$(combo_target)),-DT110_MRVL_LEGACY)

# Stock libacm references MD5_Init/Update/Final without a DT_NEEDED provider.
# Only this blob receives the platform crypto dependency; no crypto replacement.
LINKER_FORCED_SHIM_LIBS += /system/vendor/lib/libacm.so|libcrypto.so
