LOCAL_PATH := $(call my-dir)
ifeq ($(TARGET_DEVICE),goyawifi)
include $(CLEAR_VARS)
LOCAL_MODULE := lights.mrvl
LOCAL_MODULE_RELATIVE_PATH := hw
LOCAL_SRC_FILES := lights/lights.c
LOCAL_SHARED_LIBRARIES := liblog libcutils
LOCAL_CFLAGS := -Wall -Wextra
include $(BUILD_SHARED_LIBRARY)
include $(CLEAR_VARS)
LOCAL_MODULE := t110_radio_init
LOCAL_SRC_FILES := wifi/t110_load_radio_module.c
LOCAL_CFLAGS := -Wall -Wextra -std=gnu11
LOCAL_SHARED_LIBRARIES := liblog
include $(BUILD_EXECUTABLE)
include $(CLEAR_VARS)
LOCAL_MODULE := t110_bt_init
LOCAL_SRC_FILES := bluetooth/t110_bt_init.c
LOCAL_CFLAGS := -Wall -Wextra -std=gnu11
LOCAL_SHARED_LIBRARIES := liblog
include $(BUILD_EXECUTABLE)
include $(CLEAR_VARS)
LOCAL_MODULE := libbt-vendor
LOCAL_SRC_FILES := bluetooth/bt_vendor_t110.c
LOCAL_C_INCLUDES := system/bt/hci/include
LOCAL_SHARED_LIBRARIES := liblog
include $(BUILD_SHARED_LIBRARY)
include $(CLEAR_VARS)
LOCAL_MODULE := t110_stage
LOCAL_SRC_FILES := bootstrap/stage.c
LOCAL_FORCE_STATIC_EXECUTABLE := true
LOCAL_STATIC_LIBRARIES := libc
LOCAL_CFLAGS := -Wall -Wextra -Werror -std=gnu11
include $(BUILD_EXECUTABLE)
endif

# One canonical instance of each vendor EGL driver; preserve SONAME lookups.
ifeq ($(TARGET_DEVICE),goyawifi)
t110_egl_driver_names := libEGL_MRVL.so libGLESv1_CM_MRVL.so libGLESv2_MRVL.so
t110_egl_driver_links := $(addprefix $(TARGET_OUT)/vendor/lib/,$(t110_egl_driver_names))
$(t110_egl_driver_links): $(TARGET_OUT)/vendor/lib/%: $(TARGET_OUT)/vendor/lib/egl/%
	@mkdir -p $(dir $@)
	$(hide) ln -sf egl/$(notdir $@) $@
ALL_DEFAULT_INSTALLED_MODULES += $(t110_egl_driver_links)
endif
