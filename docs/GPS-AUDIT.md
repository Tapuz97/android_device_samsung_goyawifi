# GPS integration audit - original ANI7 firmware

The original firmware includes lib/hw/gps.default.so, lib/libagps_hal.so and the
android.hardware.location.gps permission. GPS is therefore an outstanding driver
integration item, not a claim that the SM-T110 has no GPS hardware.

The small gps.default.so exposes a128-byte common HMI and dynamically names
/system/lib/libagps_hal.so. That second library depends on libssl, libcrypto,
libnetutils and libmtelif in addition to the normal platform libraries. Its
mrvlGpsCallbacks object is40 bytes in the original ARM32 binary. No interface
size/callback compatibility sign-off has been made against Nougat yet.

Original mrvl_gps_platform.conf selects /dev/ttyS2 at921600 baud, GPIO/control
/proc/driver/sirf, and socket /data/system/gps. Binary strings also reference
/proc/driver/mrvgps/reset and wakeup plus private state under /data/system/gps.
Configuration disables periodic file logging by default. These paths are evidence
of expected interfaces; their presence and behavior on the preserved kernel
have not been established on the tablet in this build.

Do not blindly copy old libssl/libcrypto over Nougat's platform libraries. Both
the binary imports and the OpenSSL data/callback ABI need checking; resolved
symbol names alone would not establish compatibility. The absolute dlopen path
also needs an explicit integration plan, rather than copying the dependency to
/system/vendor/lib and assuming the loader will find it.

The first full Nougat candidate does not advertise working GPS. Preserve this
item for the functional hardware pass: inspect the actual kernel nodes, audit
the old HAL/JNI interface and dependency ABI, then integrate and validate a real
satellite fix. No tablet commands or GPS startup tests ran during this audit.
