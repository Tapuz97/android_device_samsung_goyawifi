# T110 camera/audio compatibility pass - 2026-11-13

Status: verified static ABI repairs and isolated ARM compilation; no camera,
speaker, microphone or complete ROM runtime qualification was performed.
The full build and its output verification remain owned by the parent task.

## Evidence scope

The source baseline is /root/t110-lineage14/android. Actual Samsung ANI7 binaries
were read from reference/stock-ani7/extracted. Ordinary readelf, the supplied ARM
objdump and Nougat's ARM Clang were used; REA MCP/CLI was not connected, so these
are local static/tool findings, not REA retained Evidence or observed execution.
The private evidence directory is /root/t110-lineage14/reference/hal-abi.
It contains original artifact SHA256/size identities, disassemblies, recovered
camera constant values, component compile results and vtable dumps.

## Camera ABI corrections implemented

1. **Vector/SortedVector reserved vtables.** Stock camera imports all eight
   reservedVectorImplN and all eight reservedSortedVectorImplN symbols.
   Nougat had removed them. The stock libutils Vector constructor stores mStorage,
   mCount, mFlags and mItemSize at offsets4,8,12,16; the isolated ARM probe produces
   the same offsets and sizeof20. The historical reserved slots follow the six
   real do_* virtual operations, with SortedVector's own tail after do_compare.
   All stock reserved exports point at a two-byte Thumb bx-lr body at0xdda2.
   Restoring those original intentionally empty reservations is faithful ABI
   preservation; it does not replace any vector operation or fake a successful API.
   After restoration, isolated ARM objects emit vtable sizes72/108 bytes, exactly
   matching the stock VectorImpl/SortedVectorImpl exported objects.

   Modified under T110_MRVL_LEGACY:
   - system/core/include/utils/VectorImpl.h
   - system/core/libutils/VectorImpl.cpp

   Historical primary sources:
   https://github.com/LineageOS/android_system_core/blob/cm-11.0/include/utils/VectorImpl.h
   https://github.com/LineageOS/android_system_core/blob/cm-11.0/libutils/VectorImpl.cpp

2. **MemoryBase offset constructor.** Stock camera imports the signed-long
   offset constructor; Nougat's ssize_t is signed int on ARM32. Stock constructor
   writes mSize/mOffset/mHeap at16/20/24 and constructs RefBase at28. The ARM probe
   confirms current sizeof36 and the same member offsets. Added an ARM32/T110-only
   long overload that delegates to the real ssize_t constructor, with a width
   static_assert. Both legacy and normal complete/base constructor symbols are
   emitted. No field offset or memory operation is replaced.

   Modified:
   - frameworks/native/include/binder/MemoryBase.h
   - frameworks/native/libs/binder/MemoryBase.cpp

3. **Camera parameter constants.** A standalone ARM compile of the actual
   CameraParameters.cpp against Nougat revealed25 required missing symbols, all
   static char arrays, and no missing CameraParameters operations. Their exact
   bytes were recovered from original libcamera_client.so symbol addresses and
   sizes. The device include/camera/CameraParametersExtra.h supplies them through
   Nougat's existing CAMERA_PARAMETERS_EXTRA_H/C extension. The parent added
   TARGET_SPECIFIC_HEADER_PATH to BoardConfig. A second ARM compile emits all25
   arrays with byte-for-byte stock values. This adds no instance fields.

4. **Camera HAL generation needs no fake upgrade.** The module's API is0.1.
   Nougat CameraModule.cpp explicitly supports modules below2.0 and normalizes
   their camera_info device_version to the actual HAL1 API. Its stock device's
   zero version field therefore does not require pretending it is HAL2/3.

## Audio findings and correction

- Stock audio.primary.mrvl open (function0x2d80) writes device version0x200 at
 0x2dc6 and stores it at common.version. Nougat's minimum is2.0, so it passes the
 existing generation check. No version bump or dummy modern callback was added.
- Its open-stream generation has the older trailing-argument convention.
 Nougat's additional address/source arguments are trailing on the C ABI;
 practical stream behavior and optional callback safety still need real tests.
- It imports list_init/list_add_tail/list_remove, which the built Nougat libcutils
 does not export because they became inline functions. Added
 system/core/libcutils/t110_legacy_list.c, guarded by T110_MRVL_LEGACY, exporting
 the actual current cutils/list.h operations through renamed inline calls.
 Original disassembly confirms head/item argument order and pointer updates.
 The parent added it to the target libcutils source list. The actual wrappers
 passed native32-bit ASan/UBSan initialization, append, removal and relinking
 checks. Explicit default visibility preserves their exported entry points.
- Additional root stock routing/calibration XML files were found beyond the
 previously selected asound.conf and audio/ directories: audio_path_config.xml,
 audio_gain_config.xml, audio_coeff_config.xml, audio_basic_element.xml,
 audio_swvol_config.xml, audio_swvol_element.xml and
 audio_swvol_calibration_def.xml. The parent was notified to include them.
 Original audio_policy.conf uses the pre-KitKat flat device lists rather than
 Nougat's stream-profile schema. The parent inspected this and is providing a
 Nougat-schema primary speaker/mic/wired policy with normal A2DP/USB facilities,
 instead of copying the old policy blindly. Stock audio_effects.conf may request
 extra Samsung soundfx libraries. A filename alone is not a proven read path.

## Validation and remaining limits

The real MemoryBase.cpp, VectorImpl.cpp and CameraParameters.cpp all compiled
for ARMv7 with the new declarations and platform headers in an isolated evidence
directory. No parallel make was run in the shared build output and no active
build process was stopped. The final complete shared-library link must still
show all required old/new symbols, and the entire selected blob dependency
closure must be rechecked after all18 platform libraries exist. An earlier audit
had only10 platform providers and must not be treated as a final loading failure.

These repairs establish source/ABI preconditions, not successful camera preview,
JPEG capture, video recording, speaker routing, microphone capture, headphone
switching or Bluetooth audio. Hardware access permissions, camera buffers,
kernel media interfaces, audio stream callback use and policy routing remain
part of the first complete ROM functional tests.

## Power HAL: old object boundary repaired before boot

Stock power.mrvl.so exports HMI at virtual address 0x3004 with a 140-byte
object. Its module API is 0.2 (0x0002), and hal_api_version is 0x0100. The
three real callback addresses are init 0x841, setInteractive 0xd65 and powerHint
0x843. On ARM32 these fields are at offsets 128, 132 and 136. The stock data
section ends at the end of HMI; the following BSS is not a modern callback
extension. File bytes from the later .comment section are not mapped callback
values and must not be interpreted as such.

The actual Nougat ARM-header probe yields sizeof(power_module_t)=160,
setFeature at 140, getFeature at 144 and low-power statistics fields starting
at 148. setFeature was introduced with API 0.3; the statistics callbacks arrived
with API 0.5. Both PowerManager JNI and BatteryStats JNI previously tested those
new pointers without first bounding access by the old object's version. A
non-NULL test still reads outside the 140-byte exported object.

Modified, only under T110_MRVL_LEGACY:
- frameworks/base/services/core/jni/com_android_server_power_PowerManagerService.cpp

The loader now publishes a full-sized, zero-initialized compatibility object for
API 0.2 and older modules. It copies the genuine common metadata and retains the
actual old API version. init, setInteractive and (when introduced and present)
powerHint forward to the real original callbacks with the original module as
receiver. New optional features and statistics callbacks remain NULL. Modern
modules pass through unchanged. This protects both JNI consumers; it does not
advertise double-tap-to-wake, low-power statistics or another unsupported feature.

An isolated 32-bit ASan/UBSan harness extracts this exact helper from the edited
source. It places old 140-byte API-0.2 and 136-byte API-0.1 objects immediately
before an inaccessible guard page. PASS: no out-of-bounds reads; real callback
forwarding and receiver identity; on/off and hint arguments; actual version
retained; optional callbacks NULL; modern module pass-through; NULL input.
Evidence: reference/hal-abi/power-proxy-test.cpp and power-proxy-test.json.
This is an ABI safety test, not evidence of actual tablet suspend/resume.

## Sensors HAL: legacy path already supported

Stock sensors.mrvl.so exports a 132-byte HMI object at virtual address 0x4008:
module API 0.1, only the common 128-byte prefix plus get_sensors_list. Its open
function at 0x1400 allocates its 100-byte private context, clears the original
76-byte poll-device prefix and leaves common.version zero. It installs activate,
setDelay and poll at offsets 64, 68 and 72. get_sensors_list returns one sensor
(the accelerometer); no gyroscope or other sensor is inferred from the module's
filename.

Nougat's actual ARM-header probe confirms the old poll prefix remains 76 bytes,
while later batch/flush/inject callbacks start at 76/80/84. sensor_t remains
68 bytes and sensors_event_t 104 bytes. The new module operation-mode field is
at 132, immediately beyond this old HMI object.

No sensor version bump or adapter is necessary for these observed layouts:
SensorDevice accepts the old version, uses activate/setDelay/poll, rejects
nonzero batch latency below API 1.1, and guards real batch/flush callbacks at
API 1.1. Injection and module operation-mode calls are guarded at API 1.4 before
touching those later fields. Sensor.cpp also gates FIFO descriptors above API
1.0 and max-delay/capability flags at API 1.3, preserving the legacy sensor_t
reserved area rather than treating it as newer capabilities. No sensor source
was changed. Accelerometer output, physical rotation, rate changes and behavior
across sleep/wake still require the hardware functional tests.

## Build qualification update

The parent caught that combo/select.mk resets TARGET_GLOBAL_CFLAGS. The device
now uses supported BOARD_GLOBAL_CFLAGS to enable T110_MRVL_LEGACY for target GCC
and Clang, with no host leakage. Earlier isolated ABI tests remain valid because
they explicitly supplied the macro. They do not imply that earlier full-ROM
objects had it enabled. The parent is rebuilding the real compatibility
libraries and libandroid_servers and will inspect installed artifacts before
resuming the complete image. This report does not claim that full build or any
new hardware test has finished.

## Additional audio stream blocker found after initial audit

The device API2.0 check is necessary but not sufficient. A deeper disassembly
of the actual stream constructors finds incompatible trailing callback storage:

- Stock input open at 0x3154 allocates 176 private bytes and installs the real
  common callbacks plus set_gain/read/get_input_frames_lost through offset64.
  At 0x3268 it writes its private audio-device pointer at offset68. Nougat puts
  get_capture_position at offset68. Threads.cpp's record path reads and calls
  that apparent pointer without first checking the old stream generation.
- Stock output open at 0x3bd4 allocates 152 private bytes and installs the old
  output callback prefix. It stores its private audio-device pointer at76 and
  a mutex at96. Nougat assigns set_callback at76 and presentation position at96.
  AudioStreamOutSink's timestamp path reads/tests the latter as a function
  pointer without access to the HAL device version. Direct/nonblocking paths
  can additionally touch other newer optional stream fields.

These are overlapping private data, not missing symbols. A NULL pointer test
alone cannot make these fields safe. Do not clear the stock trailing bytes in
place: doing so would corrupt real driver state. The proposed fix is a full-size
stream adapter that retains the original objects and forwards their genuine
operations with original receivers, while representing newer unsupported
callbacks as NULL in separate storage. Parent was notified before any hardware
test. The implementation and validation of this additional repair are still
pending; the earlier audio section must not be read as complete ABI sign-off.

## Audio stream adapter implemented and isolated tests passed

The additional blocker above is now repaired in:
- frameworks/av/services/audioflinger/T110AudioStreamCompat.h (new file)
- frameworks/av/services/audioflinger/AudioStreamOut.cpp
- frameworks/av/services/audioflinger/AudioFlinger.cpp

The exact gate checks T110_MRVL_LEGACY, device API2.0, module API0.1, hardware
tags, module id audio, original name "Marvll audio HW HAL" (vendor spelling)
and author "Marvell APSE/PIE". Thus normal USB/Bluetooth audio HALs retain their
usual behavior. It wraps successful opens only, and both output/input close
paths unwrap to the original objects before invoking the original HAL close.
Allocation failure closes the newly opened original stream and reports failure.

All14 real common callbacks, five original output callbacks through offset72,
and three input callbacks through64 retain actual arguments, return values and
original receiver identity. Only proven callback prefixes are inspected. Newer
optional callback slots exist in separate zero-initialized storage and stay
NULL; real private driver data is never overwritten. This preserves genuine
speaker/microphone operations rather than pretending new APIs exist.

PASS: actual ARM Clang compile with platform headers and old-prefix offset
assertions; isolated native32 ASan/UBSan guard-page objects of exactly76/68 bytes;
all22 real callback forwards; identity/arguments/results; absent callbacks stay
NULL; optional newer callbacks NULL; unwrap identity; exact metadata gate and
other-HAL rejection. Evidence: reference/hal-abi/audio-stream-proxy-test.cpp,
audio-stream-proxy-test.json, audio-stream-arm-compile.json, and stock-audio-
input/output-open.txt. No parallel full make was launched. The complete
libaudioflinger build and hardware audio operation are still pending.

## Final camera-closure signatures restored

A later closure pass found two more legacy names. Both are repaired under the
same target-only T110_MRVL_LEGACY setting:

1. GraphicBufferMapper::lock used signed int usage in ANI7; Nougat uses uint32_t.
   Added the original signed overload in native/include/ui/GraphicBufferMapper.h
   and native/libs/ui/GraphicBufferMapper.cpp. It delegates to the real unsigned
   overload, preserving every32-bit mask bit, bounds, handle, output and return
   status. The actual source ARM compile emits both exact i/j mangled exports.
   A32-bit ASan/UBSan harness of the actual extracted overload passes zero,
   ordinary flags, negative masks, INT_MIN/INT_MAX and high-bit combinations.

2. RefBase::moveReferences and ReferenceConverterBase are JB MR1 reference-
   tracking ABI. The original ReferenceMover first memmoves sp/wp objects, then
   calls this hook only to rename debug reference IDs. It is not the memory
   mover and must not perform a second memmove or change strong/weak counts.
   Restored the original converter vtable, private static signature and real
   DEBUG_REFS conditional implementation in core/include/utils/RefBase.h and
   core/libutils/RefBase.cpp. With production DEBUG_REFS=0 this is intentionally
   inactive, exactly matching stock libutils'2-byte bx-lr export at0xdda3.
   The historical debug branch renames both strong and weak IDs through the
   real mRefs methods. Actual source ARM compiles pass with DEBUG_REFS0 and
   with an isolated copy selecting DEBUG_REFS1; the exact required symbol is
   emitted. No fabricated successful result or refcount operation was added.

Historical primary sources retained in reference/hal-abi/RefBase-cm10.1.*:
https://github.com/LineageOS/android_frameworks_native/blob/cm-10.1/include/utils/RefBase.h
https://github.com/LineageOS/android_frameworks_native/blob/cm-10.1/libs/utils/RefBase.cpp
CM11's corresponding system/core sources separately preserved the old ABI hook.

Evidence: remaining-camera-abi-compile.json and mapper-usage-forward-test.json.
The parent's complete library link/closure recheck remains the final binary
qualification; these isolated compiles do not establish a camera hardware pass.

Mapper source-overload follow-up: the full build exposed an enum-to-int/uint32
ambiguity. The final source method is named lockLegacy and carries the exact old
signed lock assembler symbol, leaving the ordinary uint32 lock as the sole
source-level lock overload. This preserves binary callers without changing any
framework call site. Actual ARM compile still emits both required old/new
symbols; the32-bit forwarding harness was updated and also compiles/runs an
ordinary enum-mask call without ambiguity. Earlier wording about a public
signed overload describes the superseded first implementation.

MemoryBase source-overload follow-up: full compilation also exposed ambiguity
for unsigned size_t source offsets. The final header retains only Nougat's
original ssize_t constructor. The legacy ARM32 C1/C2 signed-long binary names
are direct assembler aliases to the matching real signed-int C1/C2 entries,
with width/signedness assertions. Thumb uses .thumb_set and ARM uses .set.
Actual source compiles in both modes. Readelf confirms matching address, size
and function type for each pair, including the Thumb entry bit (C1 0x65 and
C2 0x1 in the isolated Thumb object). Separate actual-header probes compile
both unsigned i*size and signed offsets without ambiguity. No wrapper changes
the receiver, hidden constructor arguments, virtual-base setup or return path.
The earlier delegating-long-overload wording describes a superseded version.
Evidence: reference/hal-abi/memory-constructor-alias-compile.json.
