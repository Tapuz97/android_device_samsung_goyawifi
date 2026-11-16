LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := t110_memoryheap_probe
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := memoryheap_probe.cpp
LOCAL_SHARED_LIBRARIES := libbinder libutils liblog
LOCAL_CFLAGS := -Wall -Werror
include $(BUILD_EXECUTABLE)

include $(CLEAR_VARS)
LOCAL_MODULE := t110_egl_configs
LOCAL_SRC_FILES := t110_egl_configs.c
LOCAL_SHARED_LIBRARIES := libEGL libdl
include $(BUILD_EXECUTABLE)
