# Phase2 — accelerated windows and native audio adapter

Source is implemented and component ARM checks pass. No ROM was built or flashed.

## Graphics

Patch0003 keeps Skia rendering on the GPU while removing the T110's retained-pixel
assumption: buffer age0 forces full-window damage, preserved buffers are not
requested, and ordinary eglSwapBuffers performs legacy resolve/queueing. Other
devices retain buffer-age/damage behavior. A false legacy swap with no EGL error
is now reported as failure. The previous one-pixel read remains; it is not treated
as proof of a working app window. This is a conservative compatibility candidate,
not a demonstrated diagnosis of every prior strip/text defect or a speed claim.

The actual changed swap/age callback bodies compile for ARM and pass both T110
and other-device cases under qemu-arm. Phase1 dequeue and resume fixtures also
compile and run on ARM. Full libhwui/Skia and libgui/composer builds remain pending;
controlled callback boundaries do not exercise the GPU. The old software fallback
property remains in the preserved bootstrap until a complete candidate passes
its build/content gates. The CPU-copy composer is still present.

## Native audio

implementation/audio contains a real audio.primary.t110 module and a scoped
list-operation compatibility library. The adapter translates the exact ANI7
device prefix into Android13's full structure: get_microphones was inserted at
the old dump offset. It preserves API2.0, exposes no fake modern capabilities,
retains original stream/private storage and never reads the short streams' tails.

It carries forward44100Hz primary negotiation, local HiFi keys, microphone
activation/deactivation and proper close behavior. Modern HIDL can directly call
some basic callbacks even when the old HAL left them null; the proxy supplies
truthful ENOSYS/default handling for those cases. It validates required callbacks,
module identity and open/close lifetime. See implementation/audio/AUDIO-INTEGRATION.md.

The real proxy regression uses SHORT vendor-sized stream allocations, including
the dump-offset difference, absent optional callbacks, routing preservation,
nonlocal-route isolation, unsupported rate negotiation, active-device close
rejection, failed microphone activation, standby/resume and clean closure.
It passes on ARM under QEMU and with host ASan/UBSan.

Both the HAL and list shim also compile for armv7a-linux-androideabi, link with
--no-undefined against actual shared libraries extracted from our preserved
Android13 image and export their required symbols. These Android component
builds use pinned13 hardware/system headers and retained Nougat Bionic/libc++
build headers. That distinction is intentional and recorded: they are not a
complete Android13 Soong build. GNU/Linux ARM test executables are emulation
fixtures, never installable Android artifacts.

## Remaining integration gates

- Resolve the exact vendor dependency closure and ALSA plugin paths/namespaces.
  The original libasound hardcodes system/usr plugin directories; vendor service
  permission to load them is not established by linking our new adapter itself.
- Build the full HIDL audio implementation, policy, namespace and actual ARM HWUI
  libraries in the complete pinned Android13 checkout. Validate the entire image.
- Add the verified ALSA/routing data, clock setup and narrow SELinux permissions;
  replace the product's stub only in the validated new candidate.
- Then prepare one combined physical test of accelerated screen content, sound,
  touch, radio/navigation and real suspend/wake. No flashing until these fixes and
  build gates are ready. Wi-Fi/BT/nav source is preserved, not reset to Nougat.

## Diagnostics and preservation

An initial clang14 host sanitizer binary exited during sanitizer startup with no
test output. Its verbose startup completed and all tests passed; linking the
host sanitizer test without PIE made the saved regression invocation stable.
No adapter code or bounds checks were weakened to suppress that startup issue.
Legacy header enums and missing modern callback defaults were corrected during
the ARM compilation; final saved commands all pass with warnings treated as errors.

Working14.1 source, installed/current image pair and prior rollback pair are
unchanged and reverified. Existing14.1 and Android13 backup releases remain
unpublished. Only source and small component outputs are created in this audit.
