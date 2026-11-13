# Matched Samsung ANI7 HALs plus private dependency closure. Never replace platform libc/libEGL.
PRODUCT_COPY_FILES += \
    $(LOCAL_PATH)/proprietary/lib/egl/libEGL_MRVL.so:system/vendor/lib/egl/libEGL_MRVL.so \
    $(LOCAL_PATH)/proprietary/lib/egl/libGLESv1_CM_MRVL.so:system/vendor/lib/egl/libGLESv1_CM_MRVL.so \
    $(LOCAL_PATH)/proprietary/lib/egl/libGLESv2_MRVL.so:system/vendor/lib/egl/libGLESv2_MRVL.so \
    $(LOCAL_PATH)/proprietary/lib/hw/audio.primary.mrvl.so:system/vendor/lib/hw/audio.primary.mrvl.so \
    $(LOCAL_PATH)/proprietary/lib/hw/audio_path.adda.mrvl.so:system/vendor/lib/hw/audio_path.adda.mrvl.so \
    $(LOCAL_PATH)/proprietary/lib/hw/audio_path.fm.mrvl.so:system/vendor/lib/hw/audio_path.fm.mrvl.so \
    $(LOCAL_PATH)/proprietary/lib/hw/audio_path.hifi.mrvl.so:system/vendor/lib/hw/audio_path.hifi.mrvl.so \
    $(LOCAL_PATH)/proprietary/lib/hw/audio_path.vc.mrvl.so:system/vendor/lib/hw/audio_path.vc.mrvl.so \
    $(LOCAL_PATH)/proprietary/lib/hw/audio_path.voip.mrvl.so:system/vendor/lib/hw/audio_path.voip.mrvl.so \
    $(LOCAL_PATH)/proprietary/lib/hw/audio_path.vt.mrvl.so:system/vendor/lib/hw/audio_path.vt.mrvl.so \
    $(LOCAL_PATH)/proprietary/lib/hw/camera.mrvl.so:system/vendor/lib/hw/camera.mrvl.so \
    $(LOCAL_PATH)/proprietary/lib/hw/gralloc.mrvl.so:system/vendor/lib/hw/gralloc.mrvl.so \
    $(LOCAL_PATH)/proprietary/lib/hw/hwcomposer.mrvl.so:system/vendor/lib/hw/hwcomposer.mrvl.so \
    $(LOCAL_PATH)/proprietary/lib/hw/power.mrvl.so:system/vendor/lib/hw/power.mrvl.so \
    $(LOCAL_PATH)/proprietary/lib/hw/sensors.mrvl.so:system/vendor/lib/hw/sensors.mrvl.so \
    $(LOCAL_PATH)/proprietary/lib/libGAL.so:system/vendor/lib/libGAL.so \
    $(LOCAL_PATH)/proprietary/lib/libGLESv2SC.so:system/vendor/lib/libGLESv2SC.so \
    $(LOCAL_PATH)/proprietary/lib/libHWComposerGC.so:system/vendor/lib/libHWComposerGC.so \
    $(LOCAL_PATH)/proprietary/lib/libMarvellWireless.so:system/vendor/lib/libMarvellWireless.so \
    $(LOCAL_PATH)/proprietary/lib/lib_SamsungRec_V03011b.so:system/vendor/lib/lib_SamsungRec_V03011b.so \
    $(LOCAL_PATH)/proprietary/lib/lib_Samsung_SB_AM_for_ICS_v04004.so:system/vendor/lib/lib_Samsung_SB_AM_for_ICS_v04004.so \
    $(LOCAL_PATH)/proprietary/lib/libacoustic.so:system/vendor/lib/libacoustic.so \
    $(LOCAL_PATH)/proprietary/lib/libasound.so:system/vendor/lib/libasound.so \
    $(LOCAL_PATH)/proprietary/lib/libaudiodebugtool.so:system/vendor/lib/libaudiodebugtool.so \
    $(LOCAL_PATH)/proprietary/lib/libcameraengine.so:system/vendor/lib/libcameraengine.so \
    $(LOCAL_PATH)/proprietary/lib/libcoda7542.so:system/vendor/lib/libcoda7542.so \
    $(LOCAL_PATH)/proprietary/lib/libcoda7542hal.so:system/vendor/lib/libcoda7542hal.so \
    $(LOCAL_PATH)/proprietary/lib/libcodeccoda7542enc.so:system/vendor/lib/libcodeccoda7542enc.so \
    $(LOCAL_PATH)/proprietary/lib/libcodecjpegdec.so:system/vendor/lib/libcodecjpegdec.so \
    $(LOCAL_PATH)/proprietary/lib/libcodecjpegenc.so:system/vendor/lib/libcodecjpegenc.so \
    $(LOCAL_PATH)/proprietary/lib/libgcu.so:system/vendor/lib/libgcu.so \
    $(LOCAL_PATH)/proprietary/lib/libgpucsc.so:system/vendor/lib/libgpucsc.so \
    $(LOCAL_PATH)/proprietary/lib/libgputex.so:system/vendor/lib/libgputex.so \
    $(LOCAL_PATH)/proprietary/lib/libionhelper.so:system/vendor/lib/libionhelper.so \
    $(LOCAL_PATH)/proprietary/lib/libippsp.so:system/vendor/lib/libippsp.so \
    $(LOCAL_PATH)/proprietary/lib/libippvp.so:system/vendor/lib/libippvp.so \
    $(LOCAL_PATH)/proprietary/lib/libmiscgen.so:system/vendor/lib/libmiscgen.so \
    $(LOCAL_PATH)/proprietary/lib/libphycontmem.so:system/vendor/lib/libphycontmem.so \
    $(LOCAL_PATH)/proprietary/lib/libsamsungRecord.so:system/vendor/lib/libsamsungRecord.so \
    $(LOCAL_PATH)/proprietary/lib/libsamsungSoundbooster.so:system/vendor/lib/libsamsungSoundbooster.so \
    $(LOCAL_PATH)/proprietary/lib/libsecnativefeature.so:system/vendor/lib/libsecnativefeature.so \
    $(LOCAL_PATH)/proprietary/lib/libsocketsvr.so:system/vendor/lib/libsocketsvr.so \
    $(LOCAL_PATH)/proprietary/lib/libstlport.so:system/vendor/lib/libstlport.so \
    $(LOCAL_PATH)/proprietary/etc/audio/LVVEFS_Rx_Configuration.txt:system/vendor/etc/audio/LVVEFS_Rx_Configuration.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/LVVEFS_Tx_Configuration.txt:system/vendor/etc/audio/LVVEFS_Tx_Configuration.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_BLUETOOTH_HEADSET.txt:system/vendor/etc/audio/Rx_ControlParams_BLUETOOTH_HEADSET.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_EARPIECE_WIDEBAND.txt:system/vendor/etc/audio/Rx_ControlParams_EARPIECE_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_SECVOIP_BLUETOOTH_HEADSET.txt:system/vendor/etc/audio/Rx_ControlParams_SECVOIP_BLUETOOTH_HEADSET.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_SECVOIP_EARPIECE_WIDEBAND.txt:system/vendor/etc/audio/Rx_ControlParams_SECVOIP_EARPIECE_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_SECVOIP_SPEAKER_WIDEBAND.txt:system/vendor/etc/audio/Rx_ControlParams_SECVOIP_SPEAKER_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_SECVOIP_WIRED_HEADPHONE_WIDEBAND.txt:system/vendor/etc/audio/Rx_ControlParams_SECVOIP_WIRED_HEADPHONE_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_SECVOIP_WIRED_HEADSET_WIDEBAND.txt:system/vendor/etc/audio/Rx_ControlParams_SECVOIP_WIRED_HEADSET_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_SPEAKER_WIDEBAND.txt:system/vendor/etc/audio/Rx_ControlParams_SPEAKER_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_WIRED_HEADPHONE_WIDEBAND.txt:system/vendor/etc/audio/Rx_ControlParams_WIRED_HEADPHONE_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_WIRED_HEADSET_WIDEBAND.txt:system/vendor/etc/audio/Rx_ControlParams_WIRED_HEADSET_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_BLUETOOTH_HEADSET.txt:system/vendor/etc/audio/Tx_ControlParams_BLUETOOTH_HEADSET.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_EARPIECE_WIDEBAND.txt:system/vendor/etc/audio/Tx_ControlParams_EARPIECE_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_SECVOIP_BLUETOOTH_HEADSET.txt:system/vendor/etc/audio/Tx_ControlParams_SECVOIP_BLUETOOTH_HEADSET.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_SECVOIP_EARPIECE_WIDEBAND.txt:system/vendor/etc/audio/Tx_ControlParams_SECVOIP_EARPIECE_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_SECVOIP_SPEAKER_WIDEBAND.txt:system/vendor/etc/audio/Tx_ControlParams_SECVOIP_SPEAKER_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_SECVOIP_WIRED_HEADPHONE_WIDEBAND.txt:system/vendor/etc/audio/Tx_ControlParams_SECVOIP_WIRED_HEADPHONE_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_SECVOIP_WIRED_HEADSET_WIDEBAND.txt:system/vendor/etc/audio/Tx_ControlParams_SECVOIP_WIRED_HEADSET_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_SPEAKER_WIDEBAND.txt:system/vendor/etc/audio/Tx_ControlParams_SPEAKER_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_WIRED_HEADPHONE_WIDEBAND.txt:system/vendor/etc/audio/Tx_ControlParams_WIRED_HEADPHONE_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_WIRED_HEADSET_WIDEBAND.txt:system/vendor/etc/audio/Tx_ControlParams_WIRED_HEADSET_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio_VR/LVVEFS_Rx_Configuration.txt:system/vendor/etc/audio_VR/LVVEFS_Rx_Configuration.txt \
    $(LOCAL_PATH)/proprietary/etc/audio_VR/LVVEFS_Tx_Configuration.txt:system/vendor/etc/audio_VR/LVVEFS_Tx_Configuration.txt \
    $(LOCAL_PATH)/proprietary/etc/audio_VR/Rx_ControlParams_VR_BLUETOOTH_HEADSET.txt:system/vendor/etc/audio_VR/Rx_ControlParams_VR_BLUETOOTH_HEADSET.txt \
    $(LOCAL_PATH)/proprietary/etc/audio_VR/Rx_ControlParams_VR_EARPIECE_WIDEBAND.txt:system/vendor/etc/audio_VR/Rx_ControlParams_VR_EARPIECE_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio_VR/Rx_ControlParams_VR_SPEAKER_WIDEBAND.txt:system/vendor/etc/audio_VR/Rx_ControlParams_VR_SPEAKER_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio_VR/Rx_ControlParams_VR_WIRED_HEADPHONE_WIDEBAND.txt:system/vendor/etc/audio_VR/Rx_ControlParams_VR_WIRED_HEADPHONE_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio_VR/Rx_ControlParams_VR_WIRED_HEADSET_WIDEBAND.txt:system/vendor/etc/audio_VR/Rx_ControlParams_VR_WIRED_HEADSET_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio_VR/Tx_ControlParams_VR_BLUETOOTH_HEADSET.txt:system/vendor/etc/audio_VR/Tx_ControlParams_VR_BLUETOOTH_HEADSET.txt \
    $(LOCAL_PATH)/proprietary/etc/audio_VR/Tx_ControlParams_VR_EARPIECE_WIDEBAND.txt:system/vendor/etc/audio_VR/Tx_ControlParams_VR_EARPIECE_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio_VR/Tx_ControlParams_VR_SPEAKER_WIDEBAND.txt:system/vendor/etc/audio_VR/Tx_ControlParams_VR_SPEAKER_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio_VR/Tx_ControlParams_VR_WIRED_HEADPHONE_WIDEBAND.txt:system/vendor/etc/audio_VR/Tx_ControlParams_VR_WIRED_HEADPHONE_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/audio_VR/Tx_ControlParams_VR_WIRED_HEADSET_WIDEBAND.txt:system/vendor/etc/audio_VR/Tx_ControlParams_VR_WIRED_HEADSET_WIDEBAND.txt \
    $(LOCAL_PATH)/proprietary/etc/sensor/sensord_cfg_axis:system/vendor/etc/sensor/sensord_cfg_axis \
    $(LOCAL_PATH)/proprietary/etc/firmware/mrvl/SDIO8777_SDIO_SDIO.bin:system/vendor/etc/firmware/mrvl/SDIO8777_SDIO_SDIO.bin \
    $(LOCAL_PATH)/proprietary/etc/firmware/mrvl/WlanCalData_ext.conf:system/vendor/etc/firmware/mrvl/WlanCalData_ext.conf \
    $(LOCAL_PATH)/proprietary/etc/firmware/mrvl/bt_cal_data.conf:system/vendor/etc/firmware/mrvl/bt_cal_data.conf \
    $(LOCAL_PATH)/proprietary/etc/firmware/mrvl/bt_init_cfg.conf:system/vendor/etc/firmware/mrvl/bt_init_cfg.conf \
    $(LOCAL_PATH)/proprietary/etc/firmware/mrvl/cal_data.conf:system/vendor/etc/firmware/mrvl/cal_data.conf \
    $(LOCAL_PATH)/proprietary/etc/firmware/mrvl/reg_alpha2:system/vendor/etc/firmware/mrvl/reg_alpha2 \
    $(LOCAL_PATH)/proprietary/etc/firmware/mrvl/sd8777_uapsta.bin:system/vendor/etc/firmware/mrvl/sd8777_uapsta.bin \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/MaskInfo_v2.conf:system/vendor/cameradata/ThemeShot/MaskInfo_v2.conf \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_1.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_1.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_2.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_2.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_3.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_3.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_4.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_4.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_5.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_5.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_6.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_6.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_7.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_7.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_8.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_8.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_9.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_9.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_1.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_1.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_2.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_2.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_3.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_3.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_4.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_4.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_5.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_5.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_6.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_6.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_7.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_7.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_8.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_8.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_9.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_9.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_1.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_1.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_2.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_2.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_3.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_3.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_4.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_4.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_5.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_5.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_6.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_6.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_7.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_7.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_1.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_1.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_2.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_2.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_3.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_3.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_4.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_4.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_5.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_5.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_6.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_6.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_7.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_7.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_1.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_1.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_2.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_2.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_3.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_3.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_4.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_4.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_5.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_5.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_6.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_6.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_7.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_7.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_8.yuv420p:system/vendor/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_8.yuv420p \
    $(LOCAL_PATH)/proprietary/cameradata/datapattern_420sp.yuv:system/vendor/cameradata/datapattern_420sp.yuv \
    $(LOCAL_PATH)/proprietary/cameradata/datapattern_front_420sp.yuv:system/vendor/cameradata/datapattern_front_420sp.yuv \
    $(LOCAL_PATH)/proprietary/etc/asound.conf:system/vendor/etc/asound.conf \
    $(LOCAL_PATH)/proprietary/etc/camera_profiles.xml:system/vendor/etc/camera_profiles.xml \
    $(LOCAL_PATH)/proprietary/etc/audio_basic_element.xml:system/vendor/etc/audio_basic_element.xml \
    $(LOCAL_PATH)/proprietary/etc/audio_coeff_config.xml:system/vendor/etc/audio_coeff_config.xml \
    $(LOCAL_PATH)/proprietary/etc/audio_gain_config.xml:system/vendor/etc/audio_gain_config.xml \
    $(LOCAL_PATH)/proprietary/etc/audio_path_config.xml:system/vendor/etc/audio_path_config.xml \
    $(LOCAL_PATH)/proprietary/etc/audio_swvol_calibration_def.xml:system/vendor/etc/audio_swvol_calibration_def.xml \
    $(LOCAL_PATH)/proprietary/etc/audio_swvol_config.xml:system/vendor/etc/audio_swvol_config.xml \
    $(LOCAL_PATH)/proprietary/etc/audio_swvol_element.xml:system/vendor/etc/audio_swvol_element.xml \
    $(LOCAL_PATH)/proprietary/etc/wifi/modules/mlan.ko:system/vendor/etc/wifi/modules/mlan.ko \
    $(LOCAL_PATH)/proprietary/etc/wifi/modules/sd8xxx.ko:system/vendor/etc/wifi/modules/sd8xxx.ko \
    $(LOCAL_PATH)/proprietary/etc/bluetooth/modules/mbt8xxx.ko:system/vendor/etc/bluetooth/modules/mbt8xxx.ko \
    $(LOCAL_PATH)/proprietary/firmware/mrvl/sd8777_uapsta.bin:system/vendor/firmware/mrvl/sd8777_uapsta.bin \
    $(LOCAL_PATH)/proprietary/firmware/mrvl/cal_data.conf:system/vendor/firmware/mrvl/cal_data.conf
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/LVVEFS_Rx_Configuration.txt:system/etc/audio/LVVEFS_Rx_Configuration.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/LVVEFS_Tx_Configuration.txt:system/etc/audio/LVVEFS_Tx_Configuration.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_BLUETOOTH_HEADSET.txt:system/etc/audio/Rx_ControlParams_BLUETOOTH_HEADSET.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_EARPIECE_WIDEBAND.txt:system/etc/audio/Rx_ControlParams_EARPIECE_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_SECVOIP_BLUETOOTH_HEADSET.txt:system/etc/audio/Rx_ControlParams_SECVOIP_BLUETOOTH_HEADSET.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_SECVOIP_EARPIECE_WIDEBAND.txt:system/etc/audio/Rx_ControlParams_SECVOIP_EARPIECE_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_SECVOIP_SPEAKER_WIDEBAND.txt:system/etc/audio/Rx_ControlParams_SECVOIP_SPEAKER_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_SECVOIP_WIRED_HEADPHONE_WIDEBAND.txt:system/etc/audio/Rx_ControlParams_SECVOIP_WIRED_HEADPHONE_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_SECVOIP_WIRED_HEADSET_WIDEBAND.txt:system/etc/audio/Rx_ControlParams_SECVOIP_WIRED_HEADSET_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_SPEAKER_WIDEBAND.txt:system/etc/audio/Rx_ControlParams_SPEAKER_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_WIRED_HEADPHONE_WIDEBAND.txt:system/etc/audio/Rx_ControlParams_WIRED_HEADPHONE_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Rx_ControlParams_WIRED_HEADSET_WIDEBAND.txt:system/etc/audio/Rx_ControlParams_WIRED_HEADSET_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_BLUETOOTH_HEADSET.txt:system/etc/audio/Tx_ControlParams_BLUETOOTH_HEADSET.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_EARPIECE_WIDEBAND.txt:system/etc/audio/Tx_ControlParams_EARPIECE_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_SECVOIP_BLUETOOTH_HEADSET.txt:system/etc/audio/Tx_ControlParams_SECVOIP_BLUETOOTH_HEADSET.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_SECVOIP_EARPIECE_WIDEBAND.txt:system/etc/audio/Tx_ControlParams_SECVOIP_EARPIECE_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_SECVOIP_SPEAKER_WIDEBAND.txt:system/etc/audio/Tx_ControlParams_SECVOIP_SPEAKER_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_SECVOIP_WIRED_HEADPHONE_WIDEBAND.txt:system/etc/audio/Tx_ControlParams_SECVOIP_WIRED_HEADPHONE_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_SECVOIP_WIRED_HEADSET_WIDEBAND.txt:system/etc/audio/Tx_ControlParams_SECVOIP_WIRED_HEADSET_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_SPEAKER_WIDEBAND.txt:system/etc/audio/Tx_ControlParams_SPEAKER_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_WIRED_HEADPHONE_WIDEBAND.txt:system/etc/audio/Tx_ControlParams_WIRED_HEADPHONE_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio/Tx_ControlParams_WIRED_HEADSET_WIDEBAND.txt:system/etc/audio/Tx_ControlParams_WIRED_HEADSET_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_VR/LVVEFS_Rx_Configuration.txt:system/etc/audio_VR/LVVEFS_Rx_Configuration.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_VR/LVVEFS_Tx_Configuration.txt:system/etc/audio_VR/LVVEFS_Tx_Configuration.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_VR/Rx_ControlParams_VR_BLUETOOTH_HEADSET.txt:system/etc/audio_VR/Rx_ControlParams_VR_BLUETOOTH_HEADSET.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_VR/Rx_ControlParams_VR_EARPIECE_WIDEBAND.txt:system/etc/audio_VR/Rx_ControlParams_VR_EARPIECE_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_VR/Rx_ControlParams_VR_SPEAKER_WIDEBAND.txt:system/etc/audio_VR/Rx_ControlParams_VR_SPEAKER_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_VR/Rx_ControlParams_VR_WIRED_HEADPHONE_WIDEBAND.txt:system/etc/audio_VR/Rx_ControlParams_VR_WIRED_HEADPHONE_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_VR/Rx_ControlParams_VR_WIRED_HEADSET_WIDEBAND.txt:system/etc/audio_VR/Rx_ControlParams_VR_WIRED_HEADSET_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_VR/Tx_ControlParams_VR_BLUETOOTH_HEADSET.txt:system/etc/audio_VR/Tx_ControlParams_VR_BLUETOOTH_HEADSET.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_VR/Tx_ControlParams_VR_EARPIECE_WIDEBAND.txt:system/etc/audio_VR/Tx_ControlParams_VR_EARPIECE_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_VR/Tx_ControlParams_VR_SPEAKER_WIDEBAND.txt:system/etc/audio_VR/Tx_ControlParams_VR_SPEAKER_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_VR/Tx_ControlParams_VR_WIRED_HEADPHONE_WIDEBAND.txt:system/etc/audio_VR/Tx_ControlParams_VR_WIRED_HEADPHONE_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_VR/Tx_ControlParams_VR_WIRED_HEADSET_WIDEBAND.txt:system/etc/audio_VR/Tx_ControlParams_VR_WIRED_HEADSET_WIDEBAND.txt
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/sensor/sensord_cfg_axis:system/etc/sensor/sensord_cfg_axis
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/asound.conf:system/etc/asound.conf
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/camera_profiles.xml:system/etc/camera_profiles.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/MaskInfo_v2.conf:system/cameradata/ThemeShot/MaskInfo_v2.conf
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_1.yuv420p:system/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_1.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_2.yuv420p:system/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_2.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_3.yuv420p:system/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_3.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_4.yuv420p:system/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_4.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_5.yuv420p:system/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_5.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_6.yuv420p:system/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_6.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_7.yuv420p:system/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_7.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_8.yuv420p:system/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_8.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_9.yuv420p:system/cameradata/ThemeShot/categories_v2/eye/kidscam_v2_eye_9.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_1.yuv420p:system/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_1.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_2.yuv420p:system/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_2.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_3.yuv420p:system/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_3.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_4.yuv420p:system/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_4.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_5.yuv420p:system/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_5.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_6.yuv420p:system/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_6.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_7.yuv420p:system/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_7.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_8.yuv420p:system/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_8.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_9.yuv420p:system/cameradata/ThemeShot/categories_v2/hat/kidscam_v2_hat_9.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_1.yuv420p:system/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_1.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_2.yuv420p:system/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_2.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_3.yuv420p:system/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_3.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_4.yuv420p:system/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_4.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_5.yuv420p:system/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_5.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_6.yuv420p:system/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_6.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_7.yuv420p:system/cameradata/ThemeShot/categories_v2/mouth/kidscam_v2_mouth_7.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_1.yuv420p:system/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_1.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_2.yuv420p:system/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_2.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_3.yuv420p:system/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_3.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_4.yuv420p:system/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_4.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_5.yuv420p:system/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_5.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_6.yuv420p:system/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_6.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_7.yuv420p:system/cameradata/ThemeShot/categories_v2/nose/kidscam_v2_nose_7.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_1.yuv420p:system/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_1.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_2.yuv420p:system/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_2.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_3.yuv420p:system/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_3.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_4.yuv420p:system/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_4.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_5.yuv420p:system/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_5.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_6.yuv420p:system/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_6.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_7.yuv420p:system/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_7.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_8.yuv420p:system/cameradata/ThemeShot/categories_v2/other/kidscam_v2_other_8.yuv420p
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/datapattern_420sp.yuv:system/cameradata/datapattern_420sp.yuv
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/cameradata/datapattern_front_420sp.yuv:system/cameradata/datapattern_front_420sp.yuv
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_basic_element.xml:system/etc/audio_basic_element.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_coeff_config.xml:system/etc/audio_coeff_config.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_gain_config.xml:system/etc/audio_gain_config.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_path_config.xml:system/etc/audio_path_config.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_swvol_calibration_def.xml:system/etc/audio_swvol_calibration_def.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_swvol_config.xml:system/etc/audio_swvol_config.xml
PRODUCT_COPY_FILES += $(LOCAL_PATH)/proprietary/etc/audio_swvol_element.xml:system/etc/audio_swvol_element.xml
