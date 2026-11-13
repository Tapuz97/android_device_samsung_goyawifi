/* Exact legacy Samsung ANI7 camera parameter arrays, recovered from libcamera_client.so. */
#ifndef T110_MRVL_CAMERA_PARAMETERS_EXTRA_H
#define T110_MRVL_CAMERA_PARAMETERS_EXTRA_H

#if defined(T110_MRVL_LEGACY)
#define CAMERA_PARAMETERS_EXTRA_H \
    static const char HDR_MODE_ON[]; \
    static const char ISO_MODE_50[]; \
    static const char HDR_MODE_OFF[]; \
    static const char ISO_MODE_100[]; \
    static const char ISO_MODE_200[]; \
    static const char ISO_MODE_400[]; \
    static const char ISO_MODE_800[]; \
    static const char KEY_CONTRAST[]; \
    static const char ISO_MODE_1600[]; \
    static const char ISO_MODE_3200[]; \
    static const char ISO_MODE_AUTO[]; \
    static const char KEY_SATURATION[]; \
    static const char KEY_MAX_CONTRAST[]; \
    static const char KEY_MIN_CONTRAST[]; \
    static const char KEY_MAX_SATURATION[]; \
    static const char KEY_MIN_SATURATION[]; \
    static const char PIXEL_FORMAT_YUV422P[]; \
    static const char BURST_CAPTURE_MODE_OFF[]; \
    static const char BURST_CAPTURE_MODE_FAST[]; \
    static const char KEY_SUPPORTED_HDR_MODES[]; \
    static const char KEY_MAX_BURST_CAPTURE_NUM[]; \
    static const char PIXEL_FORMAT_YUV420P_I420[]; \
    static const char PIXEL_FORMAT_YUV422I_UYVY[]; \
    static const char BURST_CAPTURE_MODE_INFINITE[]; \
    static const char KEY_SUPPORTED_BURST_CAPTURE_MODES[];

#define CAMERA_PARAMETERS_EXTRA_C \
    const char CameraParameters::HDR_MODE_ON[] = "on"; \
    const char CameraParameters::ISO_MODE_50[] = "50"; \
    const char CameraParameters::HDR_MODE_OFF[] = "off"; \
    const char CameraParameters::ISO_MODE_100[] = "100"; \
    const char CameraParameters::ISO_MODE_200[] = "200"; \
    const char CameraParameters::ISO_MODE_400[] = "400"; \
    const char CameraParameters::ISO_MODE_800[] = "800"; \
    const char CameraParameters::KEY_CONTRAST[] = "contrast"; \
    const char CameraParameters::ISO_MODE_1600[] = "1600"; \
    const char CameraParameters::ISO_MODE_3200[] = "3200"; \
    const char CameraParameters::ISO_MODE_AUTO[] = "auto"; \
    const char CameraParameters::KEY_SATURATION[] = "saturation"; \
    const char CameraParameters::KEY_MAX_CONTRAST[] = "max-contrast"; \
    const char CameraParameters::KEY_MIN_CONTRAST[] = "min-contrast"; \
    const char CameraParameters::KEY_MAX_SATURATION[] = "max-saturation"; \
    const char CameraParameters::KEY_MIN_SATURATION[] = "min-saturation"; \
    const char CameraParameters::PIXEL_FORMAT_YUV422P[] = "yuv422p"; \
    const char CameraParameters::BURST_CAPTURE_MODE_OFF[] = "off-burst"; \
    const char CameraParameters::BURST_CAPTURE_MODE_FAST[] = "fast-burst"; \
    const char CameraParameters::KEY_SUPPORTED_HDR_MODES[] = "hdr-mode-values"; \
    const char CameraParameters::KEY_MAX_BURST_CAPTURE_NUM[] = "max-burst-capture-number"; \
    const char CameraParameters::PIXEL_FORMAT_YUV420P_I420[] = "yuv420p-i420"; \
    const char CameraParameters::PIXEL_FORMAT_YUV422I_UYVY[] = "yuv422i-uyvy"; \
    const char CameraParameters::BURST_CAPTURE_MODE_INFINITE[] = "infinite-burst"; \
    const char CameraParameters::KEY_SUPPORTED_BURST_CAPTURE_MODES[] = "burst-capture-mode-values";
#endif

#endif
