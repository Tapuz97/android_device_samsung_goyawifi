"""Freeze the automatic baseline before any ROM repair; keep manual checks open."""
from pathlib import Path
from collections import Counter
import json,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/functional-audit-20261110'
assert not (e/'baseline-before-fixes.json').exists(),'Baseline already frozen; update live results without overwriting it'
doc=json.loads((e/'checklist.json').read_text());app=json.loads((e/'app-api-report.json').read_text())
assert app.get('completed') is True
results={r['id']:r for r in app['results']};items={i['id']:i for i in doc['items']};assigned=set()
def setrow(ids,status,evidence,note):
    for ident in ids.split():
        assert ident in items and ident not in assigned,ident
        assigned.add(ident);items[ident].update(status=status,evidence=evidence.split(),note=note)
setrow('CORE01','PASS','identity.txt ../offline-v40/runtime.json','Current v27 boot completed and launcher/setup operation recorded. Same boot/server remained live through this audit.')
setrow('CORE02','FAIL','runtime-errors.txt ../offline-v40/startup-keyguard-anr.txt ../offline-v40/startup-anr.txt','Startup had Keyguard/media/statement service ANRs and a SystemUI restart; boot-animation exit205.5s. Absent touch HAL lookup blocks system_server.')
setrow('CORE03','PENDING_PHYSICAL','../offline-v40/installation.json','Ordinary menu reboot is distinct from the verified recovery-to-ROM install boot. Test with owner available for recovery buttons.')
setrow('CORE04','PARTIAL','../offline-v40/installation.json','Installed recovery repeatedly entered successfully and unchanged recovery hash verified. Host rollback retained; a new destructive stock restore was not performed in this audit.')
setrow('CORE05','PASS','../offline-v40/installation.json ../offline-v40/runtime.json','v26-to-v27 image update preserved setup, preferences and separate Home/Lock wallpaper data on this tablet. General public installer is separate.')
setrow('CORE06','PASS','identity.txt app-api-report.json','User0 CE available and normal app private data/Keystore operations work.')
setrow('CORE07','PASS','app-probe-context.json app-api-report.json','QA APK installed, launched, updated, uninstalled and freshly installed as an ordinary application UID; no ROM modification.')
setrow('CORE08','PASS','settings-home-ready.xml lineage-profiles.xml ../offline-v39/navigation-runtime.json','Multiple real activities and Home/task navigation work. Prior Recents/task-selection proof uses unchanged launcher/keymap components; not a performance pass.')
setrow('CORE09','PASS','app-api-report.json','Normal app wrote/fsynced/read a16384-byte random private file and removed only its own test file.')
setrow('CORE10','PASS','app-api-report.json','Normal app generated an Android Keystore AES256 key and completed GCM encrypt/decrypt. Backend reports SOFTWARE, not hardware-backed.')
setrow('CORE11','PASS','controls.json ../offline-v40/first-v27-frame.png','Framework sleep/wake and dismissal of the existing swipe lock work. This does not validate PIN/FBE or deep suspend.')
setrow('CORE12','PENDING_PHYSICAL','user-security.txt','Credential setup/unlock must use the owner’s chosen secret; no unattended PIN or password was created.')
setrow('CORE13','FAIL','identity.txt user-security.txt','Current userdata is explicitly unencrypted. Do not describe this engineering layout as encrypted storage.')
setrow('CORE14','PARTIAL','app-api-report.json user-security.txt','Normal UID sandbox/private storage and normal permission enforcement available; comprehensive negative-access isolation testing not completed.')
setrow('CORE15','PASS','identity.txt ../../CURRENT-STATUS.md','Global SELinux Enforcing verified. Engineering su/debug exceptions remain explicitly documented; not a security certification.')
setrow('CORE16','FAIL','clock-comparison.json identity.txt','Measured wall clock differs from host by roughly4hours and timezone is Pacific/Midway. Correct configuration/RTC persistence and network time still need validation.')
setrow('CORE17','PASS','app-api-report.json','Exact elapsed-realtime wakeup alarm delivered to an ordinary app receiver. Short requested deadline is clamped by Android minimum-futurity; audible alarm is separately blocked by audio.')
setrow('CORE18','PARTIAL','app-api-report.json packages-state.txt','Runtime permission state and notification grant tested for QA package. Ordinary permission-dialog grant/deny flows not comprehensively exercised.')
setrow('CORE19','DEFERRED_RELEASE','../../community/RELEASE-CHECKLIST.md','Current engineering installer is pinned to one tablet. General model-checked clean install/rollback package belongs to the final release gate.')

setrow('INPUT01','PASS','display.txt settings-home-ready.png','Native logical600x1024, density200; physical1024x600 scanout rotation produces upright UI. Owner previously confirmed the corrected display.')
setrow('INPUT02','PASS','settings-query.png lineage-profiles.png ../offline-v40/shade-final-rest.png','Actual framebuffer captures show application, keyboard and notification content correctly after settling. Smoothness/latency is not passed.')
setrow('INPUT03','FAIL','controls.json','Android brightness requests40 and220 both left panel sysfs brightness195. A changing preference is not working backlight control.')
setrow('INPUT04','PASS','controls.json ../offline-v39/runtime.json','Framework sleep/wake changed states; same-kernel physical display wake and wallpaper restoration previously verified. Deep hardware suspend remains separate.')
setrow('INPUT05','PASS','input.txt ../offline-v39/runtime.json','Touchscreen is registered and prior owner finger confirmation uses the unchanged v29 kernel. No new finger alignment trial while owner is away.')
setrow('INPUT06','PENDING_PHYSICAL','input.txt','Multiple fingers and edge/corner alignment require a hands-on trial; capability bits alone are insufficient.')
setrow('INPUT07 INPUT08 INPUT09','PASS','input.txt ../offline-v39/navigation-runtime.json','Owner explicitly confirmed all three physical keys; v27 retains the exact kernel/keymaps and navigation policy. No new finger trial claimed.')
setrow('INPUT10','PENDING_PHYSICAL','input.txt','Volume keys are mapped/registered; verify physical operation and audible effect after audio is ported.')
setrow('INPUT11','PARTIAL','input.txt controls.json','Physical power/recovery use previously works and framework sleep/wake works. Power menu/shutdown/long-press behavior needs the remaining dedicated checks.')
setrow('INPUT12 INPUT13','PASS','../offline-v39/navigation-runtime.json lineage-buttons.xml','Native Buttons toggle and exclusive modes were exercised on the unchanged policy/keymap components. Current hardware mode0 retained; full finger recheck is in owner handoff.')
setrow('INPUT14','FAIL','sensors.txt app-api-report.json','Kernel accelerometer input exists but Android SensorService has zero sensors; automatic sensor rotation cannot work.')
setrow('INPUT15','PENDING_PHYSICAL','usb.txt','External keyboard/mouse and OTG capability need owner accessories and physical connection.')

setrow('POWER01','PASS','battery.txt','Battery level/status traverse the Health service and agree with current sysfs. This does not prove current calibration or charging current accuracy.')
setrow('POWER02','PASS','battery.txt','USB-online state is1 and BatteryService reports USB powered. Actual charge delivery is a separate physical check.')
setrow('POWER03','PENDING_PHYSICAL','battery.txt','Wall charger, cable removal/reinsertion and sustained charge delivery need owner observation.')
setrow('POWER04','PASS','battery.txt','Battery health/temperature/voltage are exposed with plausible readings. External calibration and legacy current-unit interpretation remain unqualified.')
setrow('POWER05','PENDING_PHYSICAL','power.txt','Screen-off is not deep suspend. USB/wake-count read can block; test unplugged idle and physical wake when owner is available.')
setrow('POWER06','PENDING_PHYSICAL','../../patches/0074-kernel-goya-touch-in-charger-boot.patch','Full Android charging-related boot is patched. Stock-style powered-off charging behavior has not been qualified.')
setrow('POWER07','PENDING_PHYSICAL','identity.txt','Do not shut down an unattended tablet that needs a physical button to restart.')
setrow('POWER08','PARTIAL','lineage-services.txt','Android ThermalService reports HAL Ready:false/no cached temperatures. Kernel-level protection and external thermal behavior not qualified.')

setrow('AUDIO01 AUDIO02','FAIL','audio.txt ../../work/device/samsung/t110_bringup/t110_system.mk','Product deliberately uses a silent generic primary audio fallback; real speaker/microphone hardware routing is unported.')
setrow('AUDIO03 AUDIO04','BLOCKED','audio.txt','Needs real audio HAL/routing, then owner headset insertion and observation. Kernel jack input alone does not prove sound.')
setrow('AUDIO05','PARTIAL','audio.txt profiles-default-verified.xml','Software ringer/profile controls operate. Audible volume/mute cannot pass with a silent primary HAL.')
setrow('AUDIO06 AUDIO08 AUDIO10','BLOCKED','audio.txt','End-to-end focus/alarm/recording requires functional audio input/output; app/service presence is not a pass.')
setrow('AUDIO07 AUDIO09','FAIL','app-api-report.json media-start-errors.txt','Normal app H264 and AAC decoder starts failed, including explicitly requested OMX names (which may alias Codec2). Real sound is also unavailable. No working playback claim.')

setrow('CAM01','FAIL','camera.txt app-api-report.json','CameraService and ordinary Camera2 API enumerate zero cameras; no provider/HAL installed.')
setrow('CAM02 CAM03 CAM04 CAM05 CAM06 CAM07','BLOCKED','camera.txt ../offline-v39/camera-and-lag-findings.md','Blocked by CAM01, kernel coherent capture allocation and missing provider/format/gralloc integration. Do not count opening a camera app as capture working.')
setrow('CAM08','NOT_APPLICABLE','hardware-baseline.md','Samsung documents a rear camera only for this model; front camera and flash are not release targets.')

setrow('NET01','FAIL','wifi.txt wifi-toggle-test.txt hal-services.txt','No usable Wi-Fi interface, vendor HAL object is null and STA start fails.')
setrow('NET02','FAIL','wifi-toggle-test.txt','Explicit enable request returned to disabled with no wlan interface; original disabled state restored.')
setrow('NET03 NET04 NET05 NET06 NET07 NET09','BLOCKED','wifi.txt wifi-toggle-test.txt','Requires NET01/NET02. No access-point credentials requested or changed; hotspot support needs separate capability validation after the driver works.')
setrow('NET08','PARTIAL','connectivity.txt wifi.txt','Airplane-mode state exists; usable Wi-Fi override cannot pass while Wi-Fi cannot start.')
setrow('NET10','FAIL','bluetooth.txt kernel-capabilities.txt features.txt','No BluetoothManager service/advertised Bluetooth support or active adapter; driver/feature/HAL integration incomplete.')
setrow('NET11 NET12 NET13 NET14','BLOCKED','bluetooth.txt','Requires Bluetooth stack first; pairing/audio/HID/BLE will also need owner accessories and peer devices.')
setrow('NET15','BLOCKED','connectivity.txt','Network services exist but no usable uplink. End-to-end IP/VPN operations are not qualified.')

setrow('HW01','FAIL','location.txt features.txt','Only passive/fused software providers; no GNSS provider/fix despite documented GPS+GLONASS hardware.')
setrow('HW02','PARTIAL','location.txt','Location settings/permission infrastructure exists; actual position delivery blocked by HW01.')
setrow('HW03','FAIL','sensors.txt app-api-report.json','Ordinary app finds no accelerometer and SensorService reports devInitCheck -19; kernel input alone is not Android sensor support.')
setrow('HW04','NOT_APPLICABLE','hardware-baseline.md','Samsung lists only accelerometer. Do not invent gyro/ambient-light/compass support based on generic Android menus.')
setrow('HW05','CAPABILITY_REVIEW','hardware-baseline.md kernel-capabilities.txt','Vibration is not documented in the original model manual and drivers are disabled. Confirm fitted hardware before treating absence as a porting defect.')
initial=json.loads((e/'app-api-initial.json').read_text());had_initial_fail=any(r['id']=='shared-app-storage' and r['status']=='FAIL' for r in initial['results'])
setrow('HW06','PARTIAL' if had_initial_fail else 'PASS','app-api-initial.json app-api-report.json app-api-before-fresh.json','Shared app storage passed subsequent normal-UID and fresh-install roundtrips without a ROM change. Initial first-use getExternalFilesDir returned null; reliability/cold-boot regression remains open.')
setrow('HW07','PASS','app-api-report.json','Normal app inserted, wrote and read its own MediaStore PNG, then removed it. This validates basic provider media storage, not every gallery/indexing workflow.')
setrow('HW08','PARTIAL','storage.txt app-api-report.json','Shared volume mounted and MediaStore operations work. Complete DocumentsUI/SAF picker grant/create/open workflow not yet qualified.')
setrow('HW09 HW10','PENDING_PHYSICAL','storage.txt hardware-baseline.md','No external media currently attached. Owner has microSD/OTG accessories but is away; no reformatting or data changes attempted.')
setrow('HW11','PASS','app-probe-context.json collection.json','USB ADB remained connected, transferred the QA APK and data, and executed commands on the identified tablet.')
setrow('HW12 HW13','FAIL','usb.txt','Kernel gadget exposes MTP/PTP nodes, but Android USB service is absent and active mode is ADB only. Public MTP/function selection/reconnect not implemented.')

setrow('APP01','PASS','../offline-v39/runtime.json ../offline-v39/navigation-runtime.json','Launcher/setup, drawer and task navigation previously exercised with unchanged launcher APK; ordinary launches work in current boot. No smoothness pass.')
setrow('APP02','PASS','settings-home-ready.png lineage-trust.xml lineage-buttons.xml lineage-profiles.xml','Settings homepage, search and sampled native Lineage pages open. This is scoped to observed pages, not every Settings entry.')
setrow('APP03','PASS','settings-query.xml settings-query.png','Native Settings search indexes and displays Wi-Fi results without the old crash. Result-navigation details are recorded in UI audit notes; no blanket indexing coverage claim.')
setrow('APP04','PASS','settings-query.png ime.txt','Native LatinIME visibly opens with correct keys and the search editor accepts text. Physical-finger typing remains in owner handoff.')
setrow('APP05','PASS','app-api-report.json','Foreground clipboard roundtrip passed, previous clipboard restored without logging its contents.')
setrow('APP06','PASS','app-api-report.json ../offline-v40/runtime.json','Ordinary app post/cancel passed; native shade/expand/collapse/scroll rendering was separately verified on current v27.')
setrow('APP07','PARTIAL','../offline-v40/shade-final-rest.png wifi-toggle-test.txt','Shade/tiles render; tiles depending on missing Wi-Fi/sensors cannot provide working functions.')
setrow('APP08','PARTIAL','app-api-report.json features.txt','Clock package exists and app-level alarm delivery passed. End-to-end Clock UI timer and audible alert remain unqualified/blocked by audio.')
setrow('APP09','PASS','app-api-report.json','Real WebView local HTML/JavaScript execution passed in a normal app UID. Internet browsing blocked by Wi-Fi; not a network pass.')
widget=results['widget-host'];setrow('APP10','PASS' if widget['status']=='PASS' else 'PARTIAL','app-api-report.json codec-widget-storage-details.txt','QA widget test result: '+widget['detail']+' Native launcher drag/placement ergonomics remain a hands-on/UI check.')
setrow('APP11','PASS','app-api-report.json','Normal app created/read/deleted only its own temporary local contact, calendar and event. No online account sync claim.')
setrow('APP12','PARTIAL','accessibility.txt settings-home-ready.xml','Accessibility manager/UIAutomation hierarchy retrieval works. No spoken accessibility service installed; speech/navigation qualification needs functional audio and owner testing.')
setrow('APP13','FAIL','controls.json framework-capture-hang.txt','Normal screenshot capture failed to return/save a PNG and stalled in GraphicBuffer import; direct framebuffer diagnostic images are not a screenshot-function pass.')
setrow('APP14','PARTIAL','packages-state.txt','Default native Home/IME/camera resolutions work. Role-switch/default-app selection UI not comprehensively exercised.')
setrow('APP15','BLOCKED','features.txt ../../community/RELEASE-CHECKLIST.md','Backup app is installed; backup destination, actual backup/restore and public rollback still require validation. Installation is not a backup pass.')
setrow('APP16','BLOCKED','connectivity.txt','No network uplink for a real download. File/provider opening is only partially covered by MediaStore tests.')

setrow('LOS01','PASS','lineage-buttons.xml ../offline-v39/navigation-runtime.json','Native Buttons page and mutual exclusion changes were actually exercised on identical navigation components. Arbitrary extra key actions not all tested.')
setrow('LOS02','PASS','lineage-trust.xml user-security.txt','Native Trust dashboard/alerts open and expose the engineering security state; alerts are not a claim of secure production configuration.')
setrow('LOS03','PASS','../offline-v39/runtime.json ../offline-v40/runtime.json','Native collection/preview/Apply and separate Home/Lock images verified, exact ThemePicker retained in v27. HQ artwork upgrades are phase2.')
setrow('LOS04','PARTIAL','../offline-v40/shade-final-rest.png','Existing status/Quick Settings functions are present; backend-dependent tile actions fail with their missing hardware. Appearance configuration is deferred.')
setrow('LOS05','PASS','profiles-silent-verified.xml profiles-default-verified.xml','Native profile radio selection changed to Silent and back to Default; original normal ringer/profile restored. Missing hardware effects remain blocked by their own rows.')
setrow('LOS06','DEFERRED_NONFUNCTIONAL','lineage-services.txt','Service advertises software color/reader capabilities. Visual color-temperature/appearance qualification belongs to the later UI/feature pass as requested.')
setrow('LOS07 LOS08','BLOCKED','audio.txt','AudioFX/Recorder cannot pass real sound/recording functions until the audio HAL and routing work.')
setrow('LOS09','PARTIAL','user-security.txt app-api-report.json','Permission infrastructure/private sandbox/notification access work; full privacy controls and secure credential flows not all tested.')
setrow('LOS10','PARTIAL','input.txt','Native global-actions service exists and physical power is mapped. Actual shutdown/reboot requires the owner available for restart/recovery.')
setrow('LOS11','DEFERRED_RELEASE','../../community/RELEASE-CHECKLIST.md ../offline-v40/installation.json','Engineering update on this unit verified; no general OTA feed/public update package. Do not present native updater availability as functioning OTA delivery.')
setrow('LOS12','BLOCKED','connectivity.txt','No configured online sync account and no usable network. Local contacts/calendar storage passed separately.')
setrow('LOS13','PARTIAL','usb.txt media-start-errors.txt','ADB/developer operation works, but USB framework service is missing, auth socket type mismatch loops and standalone Java CLI tools need explicit runtime environment in this bring-up.')
setrow('LOS14','PENDING_PHYSICAL','input.txt ../../work/device/samsung/t110_bringup/overlay/lineage-sdk/lineage/res/res/values/config.xml','Supported hardware wake/gesture options require physical noninteractive testing. Do not promise unsupported screen-off gestures.')
setrow('SCOPE01','NOT_APPLICABLE','hardware-baseline.md','SM-T110 is Wi-Fi-only; calls/SIM/SMS/mobile data are not missing port functions.')
setrow('SCOPE02','NOT_APPLICABLE','hardware-baseline.md','NFC/fingerprint/IR are not documented fitted hardware targets for this model; generic framework services do not prove presence.')
setrow('SCOPE03','PASS','features.txt','No GMS/Play Store bundle is claimed or required. Google-named AOSP camera-extension components do not constitute a Google-apps installation.')
setrow('SCOPE04','PASS','identity.txt','Audit targets Android13/API33/Lineage20 and the fitted SM-T110 hardware, not features added in later Android versions.')

assert assigned==set(items),sorted(set(items)-assigned)
doc.update(phase='AUTOMATIC_AUDIT_COMPLETE_REMOTE_FIXES_AUTHORIZED',baseline_frozen_at_host_epoch=time.time(),all_functional_work_complete=False,physical_checks_complete=False,repair_gate='Owner subsequently authorized fixes not requiring intervention; hands-on checks remain pending. No UI/HQ wallpaper phase until functional work is complete.',summary=dict(Counter(i['status'] for i in doc['items'])))
assert all(i['status']!='NOT_CHECKED' and i['note'] for i in doc['items'])
(e/'checklist.json').write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
(e/'baseline-before-fixes.json').write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
lines=['# Functional checklist — SM-T110 Android13 / LineageOS20','',
'Automatic assessment complete; **functional work is NOT complete**. Physical checks remain open.',
'The owner subsequently authorized applying fixes that do not need their intervention.',
'No UI polish, speed-tuning, extra features or HQ wallpaper work until the functional phase is complete.','',
'Only PASS is ticked. PARTIAL/FAIL/BLOCKED/PENDING are not passes. N/A and deferred release/appearance items are classified separately.',
'Working claims are limited to the evidence and scope written below; service/package presence alone is not validation.','',
'Counts: '+', '.join(f'{k}={v}' for k,v in doc['summary'].items())+'.','',
'Evidence: [audit records](evidence/functional-audit-20261110/), including normal-UID API tests and real framebuffer/UI captures.',
'Baseline build: system v27 / BOOT v29; no new firmware was flashed to perform this assessment.','']
last=None
for item in doc['items']:
    if item['group']!=last:lines+=['## '+item['group'],''];last=item['group']
    tick='x' if item['status']=='PASS' else ' '
    refs=', '.join('[evidence](evidence/functional-audit-20261110/'+v+')' for v in item['evidence'])
    lines+=[f'- [{tick}] **{item["id"]} {item["function"]} — {item["status"]}**. {item["note"]} {refs}']
lines+=['','## Next repair order','',
'1. Nonblocking startup hardware probes, codec buffer allocation and graphics buffer-import failures.',
'2. Real brightness/lights, USB framework integration and storage first-use reliability.',
'3. Wi-Fi/Bluetooth, accelerometer/GNSS, audio hardware and camera driver/provider/gralloc integration.',
'4. Owner-assisted physical checks, repeat boot/suspend and accessory validation.',
'5. Only after functional completion: UI/performance/extra feature polish and higher-quality wallpapers in native Lineage settings.','',
'This baseline is preserved in baseline-before-fixes.json. Update results only after a repair is built/installed and the relevant function actually retested.']
(p/'FUNCTIONAL-CHECKLIST.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(doc['summary'],indent=2));print('AUTOMATIC_AUDIT_FROZEN_BEFORE_REPAIRS')
