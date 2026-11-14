from pathlib import Path
import json,hashlib,shutil,subprocess,xml.etree.ElementTree as ET,zipfile
r=Path('/root/t110-android13-audit');out=r/'device/development/android13-audit-20261114';dest=r/'arm-checks'
local=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/android13-audit')
for name in ('prepare_arm_headers.py','prepare_audio_adapter.py','check_audio_arm.py','check_graphics_arm.py','link_audio_android.py','fix_accelerated_windows.py','record_phase2.py'):
 shutil.copy2(local/name,out/name)
shutil.copy2(local/'LegacyListTest.cpp',out/'tests/LegacyListTest.cpp')
proof=out/'arm-verification';proof.mkdir(exist_ok=True)
for name in ('audio-results.json','graphics-results.json','android-link-results.json'):
 data=json.loads((dest/name).read_text());assert all(x.get('exit',0)==0 for x in data),name
 shutil.copy2(dest/name,proof/name)
# Exact Android13 header content and upstream pins, separately from legacy build headers.
pins={x['path']:x['head'] for x in json.loads((r/'restored/source-delta/projects.json').read_text())}
headers=[]
for p in sorted((r/'arm-headers').rglob('*.h')):
 headers.append(dict(path=str(p.relative_to(r/'arm-headers')),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(proof/'headers.json').write_text(json.dumps(dict(pins={p:pins[p] for p in ('hardware/libhardware','system/media','system/core')},files=headers),indent=2)+'\n')
# XML topology/profile checks for the integration input, not schema/policy build qualification.
tree=ET.parse(out/'implementation/audio/primary_audio_policy_configuration.xml').getroot()
assert tree.get('halVersion')=='2.0'
ports={x.get('name',x.get('tagName')) for x in tree.findall('./mixPorts/mixPort')+tree.findall('./devicePorts/devicePort')}
for route in tree.findall('./routes/route'):
 assert route.get('sink') in ports and all(x in ports for x in route.get('sources').split(','))
assert tree.find('./mixPorts/mixPort/profile').get('samplingRates')=='44100'
artifacts={}
for name in ('audio.primary.t110.so','libt110_audio_legacy_compat.so'):
 p=dest/name;artifacts[name]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
summary=dict(status='COMPONENT_ARM_CHECKS_PASS_FULL_PLATFORM_AND_HARDWARE_PENDING',graphics='Device-only full redraw/ordinary swap candidate; callback ARM emulation passed',audio='Complete ARM Android forwarding module and list shim compiled/linked against preserved Android13 providers; proxy regressions pass',artifacts=artifacts,flashed=False,rom_image_built=False,full_libHWUI_built=False,real_vendor_module_loaded=False,product_selection_changed=False,selinux_policy_compiled=False)
(proof/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
notes='''# Phase2 — accelerated windows and native audio adapter

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
'''
(out/'PHASE2.md').write_text(notes)
read=out/'README.md';s=read.read_text();prefix='''# Current progress: ARM audio module and GPU-window candidate

See [PHASE2.md](PHASE2.md) and [arm-verification/SUMMARY.json](arm-verification/SUMMARY.json).
The real forwarding audio module now exists and links as Android ARM code.
Full platform, vendor-loader and physical qualification remain pending. The older
first-pass findings below describe the preserved baseline, not missing phase2 source.

---

'''
if not s.startswith('# Current progress:'):read.write_text(prefix+s)
shutil.copytree(out,local/'report',dirs_exist_ok=True)
# A small component checkpoint; no stock/system provider binaries or personal data.
payload=local/'component-backup';payload.mkdir(exist_ok=True)
zip_path=payload/'t110-android13-offline-components-20261114.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
 for name in artifacts:z.write(dest/name,'components/'+name)
 for p in proof.glob('*.json'):z.write(p,'verification/'+p.name)
 z.write(out/'PHASE2.md','PHASE2.md')
with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None
(payload/'SHA256SUMS.txt').write_text(hashlib.sha256(zip_path.read_bytes()).hexdigest()+'  '+zip_path.name+'\n')
print('Saved phase2 source, exact ARM checks and small component archive:',zip_path)
