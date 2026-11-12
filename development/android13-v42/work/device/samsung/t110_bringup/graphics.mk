PRODUCT_PACKAGES += \
    t110_libGAL \
    t110_libgputex \
    t110_libgcu \
    t110_libHWComposerGC \
    t110_libstdcpp \
    t110_libEGL_MRVL \
    t110_libGLESv1_CM_MRVL \
    t110_libGLESv2_MRVL \
    t110_libGLESv2SC \
    t110_gralloc_mrvl \
    t110_hwcomposer_mrvl \
    libt110_gralloc_binder_compat \
    android.hardware.graphics.composer@2.1-service \
    android.hardware.graphics.allocator@2.0-service \
    android.hardware.graphics.allocator@2.0-impl \
    android.hardware.graphics.mapper@2.0-impl
PRODUCT_VENDOR_PROPERTIES += ro.hardware.egl=MRVL ro.hardware.gralloc=mrvl
PRODUCT_SYSTEM_PROPERTIES += ro.t110.legacy_gpu=true
# The stock GLES2 driver cannot import every format used by shader warmup.
# This optional optimization aborts in Skia before ordinary RGBA rendering.
PRODUCT_SYSTEM_PROPERTIES += service.sf.prime_shader_cache=0

# Use the GLES2-era compositor with this 2013 Vivante driver. Its EGL image
# and framebuffer path avoids Skia's newer AHardwareBuffer rendering path.
PRODUCT_SYSTEM_PROPERTIES += debug.renderengine.backend=gles
# The saved boot log shows invalid Vivante objects during zygote preloading.
# Initialize the driver independently after fork in each application instead.
PRODUCT_SYSTEM_PROPERTIES += ro.zygote.disable_gl_preload=true
