LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := t110_memoryheap_probe
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := memoryheap_probe.cpp
LOCAL_SHARED_LIBRARIES := libbinder libutils liblog
LOCAL_CFLAGS := -Wall -Werror
include $(BUILD_EXECUTABLE)
