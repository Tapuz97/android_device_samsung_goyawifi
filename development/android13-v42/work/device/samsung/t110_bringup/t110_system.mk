# Compile the full Android/Lineage system independently of boot/HAL integration.
# BUILD ONLY: this product is not yet a flashable or hardware-qualified ROM.
TARGET_SCREEN_WIDTH := 600
TARGET_SCREEN_HEIGHT := 1024
TARGET_BOOTANIMATION_HALF_RES := true
# Patch 0043 also selects this in the separately evaluated runtime product node.
# Debug ART takes precedence
# over persist.sys.dalvik.vm.lib.2 whenever libartd is installed on an eng build.
# Keep debugging access, but use the standard optimized runtime on the Cortex-A9.
PRODUCT_ART_TARGET_INCLUDE_DEBUG_BUILD := false
SOONG_CONFIG_NAMESPACES += t110
SOONG_CONFIG_t110 += preopt_flattened_apex_apps preopt_apex_name
SOONG_CONFIG_t110_preopt_flattened_apex_apps := true
SOONG_CONFIG_t110_preopt_apex_name := com.android.permission com.android.tethering com.android.btservices
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base.mk)
$(call inherit-product, vendor/lineage/config/common_full_tablet_wifionly.mk)
$(call inherit-product, frameworks/native/build/tablet-7in-hdpi-1024-dalvik-heap.mk)

PRODUCT_NAME := lineage_t110_system
PRODUCT_DEVICE := t110_bringup
PRODUCT_BRAND := samsung
PRODUCT_MODEL := SM-T110
PRODUCT_MANUFACTURER := samsung
PRODUCT_SHIPPING_API_LEVEL := 17
PRODUCT_USE_DYNAMIC_PARTITIONS := false
PRODUCT_ENFORCE_VINTF_MANIFEST := false
PRODUCT_AAPT_CONFIG := normal
PRODUCT_AAPT_PREF_CONFIG := mdpi
PRODUCT_SYSTEM_PROPERTIES += ro.t110.legacy_processgroups=true ro.t110.legacy_usb=true
# Recovery uses Samsung's PMIC reboot target; this board has no misc partition.
PRODUCT_SYSTEM_PROPERTIES += ro.t110.reboot_without_misc=true
# Engineering compatibility for the pre-eBPF kernel; network policy/offload is unvalidated.
PRODUCT_SYSTEM_PROPERTIES += ro.t110.legacy_bpf=true
# No modern GNSS provider is ported yet. Probe declared, already-ready services
# without making the system-server main thread wait for absent legacy HALs.
PRODUCT_SYSTEM_PROPERTIES += ro.t110.optional_hal_probe=true
PRODUCT_SYSTEM_PROPERTIES += ro.sf.lcd_density=200
# The framebuffer adapter exposes natural 600x1024 and applies the stock
# fixed panel rotation at scanout. Do not rotate a second time in SurfaceFlinger.
PRODUCT_SYSTEM_PROPERTIES += ro.surface_flinger.primary_display_orientation=ORIENTATION_0
PRODUCT_PACKAGES += t110_bionic_probe t110_path_probe t110_processgroup_probe
PRODUCT_PACKAGES += android.hardware.keymaster@4.1-service android.hardware.gatekeeper@1.0-service.software

# Engineering audio fallback: keeps framework audio services alive. This stub
# does not drive the T110 speaker or microphone; native audio remains unported.
PRODUCT_PACKAGES += android.hardware.audio.service \
    android.hardware.audio@7.1-impl \
    android.hardware.audio.effect@7.0-impl \
    audio.primary.default audio.r_submix.default
PRODUCT_COPY_FILES += \
    frameworks/av/services/audiopolicy/config/audio_policy_configuration_generic.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio_policy_configuration.xml \
    frameworks/av/services/audiopolicy/config/primary_audio_policy_configuration_7_0.xml:$(TARGET_COPY_OUT_VENDOR)/etc/primary_audio_policy_configuration.xml \
    frameworks/av/services/audiopolicy/config/r_submix_audio_policy_configuration.xml:$(TARGET_COPY_OUT_VENDOR)/etc/r_submix_audio_policy_configuration.xml \
    frameworks/av/services/audiopolicy/config/audio_policy_volumes.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio_policy_volumes.xml \
    frameworks/av/services/audiopolicy/config/default_volume_tables.xml:$(TARGET_COPY_OUT_VENDOR)/etc/default_volume_tables.xml \
    frameworks/av/services/audiopolicy/config/surround_sound_configuration_5_0.xml:$(TARGET_COPY_OUT_VENDOR)/etc/surround_sound_configuration_5_0.xml

LOCAL_PATH := device/samsung/t110_bringup
$(call inherit-product, $(LOCAL_PATH)/graphics.mk)

# Linux 3.4 lacks the memfd dual-view mapping required by system-server JIT.
# Keep AOT/interpreter execution; do not enter the failed private JIT region.
PRODUCT_SYSTEM_PROPERTIES += dalvik.vm.usejit=false dalvik.vm.usejitprofiles=false
# JIT is unavailable on this kernel; compile first-boot permission/UI code on
# the build machine instead of running it through the interpreter on the tablet.
PRODUCT_DEXPREOPT_SPEED_APPS += PermissionController SystemUI TrebuchetQuickStep Settings ThemePicker
# These services run during startup and ART cannot use JIT on this kernel.
PRODUCT_DEXPREOPT_SPEED_APPS += NetworkStack TetheringNext
PRODUCT_DEXPREOPT_SPEED_APPS += Bluetooth
# The engineering build's extra main-thread diagnostics flash a red frame on
# routine disk access. Keep debugging access without enabling those defaults.
PRODUCT_SYSTEM_PROPERTIES += persist.sys.strictmode.disable=true

# BatteryService requires a registered Health HAL. Use the standard sysfs monitor.
PRODUCT_PACKAGES += android.hardware.health@2.1-service android.hardware.health@2.1-impl

# Use Android's standard lights service with the actual panel backlight node.
# Only panel BACKLIGHT is exposed until the capacitive-key LED control is ported.
PRODUCT_PACKAGES += android.hardware.light@2.0-service android.hardware.light@2.0-impl lights.mrvl
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/lights/init.t110.lights.rc:$(TARGET_COPY_OUT_VENDOR)/etc/init/init.t110.lights.rc

# Keep the native WifiService, wificond and AIDL supplicant on the device.
# The SDIO driver is loaded by a board service after ueventd is available.
PRODUCT_PACKAGES += t110_radio_init wpa_supplicant
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.wifi.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.wifi.xml \
    external/wpa_supplicant_8/wpa_supplicant/wpa_supplicant_template.conf:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/wpa_supplicant.conf \
    $(LOCAL_PATH)/wifi/assets/mlan.ko:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/modules/mlan.ko \
    $(LOCAL_PATH)/wifi/assets/sd8xxx.ko:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/modules/sd8xxx.ko \
    $(LOCAL_PATH)/wifi/assets/sd8777_uapsta.bin:$(TARGET_COPY_OUT_VENDOR)/firmware/mrvl/sd8777_uapsta.bin \
    $(LOCAL_PATH)/wifi/assets/cal_data.conf:$(TARGET_COPY_OUT_VENDOR)/firmware/mrvl/cal_data.conf

# Use the standard Android Bluetooth HAL/stack over the qualified Marvell H4
# character transport. The board loader reuses Wi-Fi's active combo firmware.
PRODUCT_PACKAGES += t110_bt_init libbt-vendor.t110 android.hardware.bluetooth@1.1-service
PRODUCT_PACKAGES += android.hardware.bluetooth.audio@2.1-impl
PRODUCT_SYSTEM_PROPERTIES += ro.bt.bdaddr_path=/data/vendor/t110-bluetooth/controller_address
PRODUCT_SYSTEM_PROPERTIES += ro.bluetooth.a2dp_offload.supported=false
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.bluetooth.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.bluetooth.xml \
    frameworks/native/data/etc/android.hardware.bluetooth_le.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.bluetooth_le.xml \
    $(LOCAL_PATH)/bluetooth/assets/mbt8xxx.ko:$(TARGET_COPY_OUT_VENDOR)/etc/bluetooth/modules/mbt8xxx.ko \
    $(LOCAL_PATH)/storage/fstab.mrvl:$(TARGET_COPY_OUT_VENDOR)/etc/fstab.mrvl

# Samsung's Jelly Bean sdcardfs rejects the modern fsuid/fsgid/mask options.
# Select Android's existing MediaProvider FUSE path. Keep its access checks;
# do not require newer ext4 casefold/project-quota features on existing data.
PRODUCT_SYSTEM_PROPERTIES += external_storage.sdcardfs.enabled=false

# Device overlays accompany the temporary software Canvas window fallback.
DEVICE_PACKAGE_OVERLAYS += device/samsung/t110_bringup/overlay

# Trebuchet requires the framework widget service. Without this declaration,
# SystemServer omits it and the launcher loader repeatedly crashes.
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.software.app_widgets.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.software.app_widgets.xml \
    frameworks/native/data/etc/android.hardware.touchscreen.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.touchscreen.xml

# Board-specific navigation codes. Generic.kl treats Linux KEY_HOME as MOVE_HOME.
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/keylayout/gpio-keys.kl:$(TARGET_COPY_OUT_VENDOR)/usr/keylayout/gpio-keys.kl \
    $(LOCAL_PATH)/keylayout/sec_touchscreen.kl:$(TARGET_COPY_OUT_VENDOR)/usr/keylayout/sec_touchscreen.kl
