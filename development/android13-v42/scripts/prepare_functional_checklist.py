"""Create the audit inventory before assessment; evidence is required to tick PASS."""
from pathlib import Path
import json
p=Path(__file__).resolve().parents[1];e=p/'evidence/functional-audit-20261110';e.mkdir(parents=True,exist_ok=True)
groups={
'Boot, runtime and security':[
('CORE01','Boot reaches Android and launcher'),('CORE02','Startup completes without service ANRs or automatic restarts'),('CORE03','Ordinary reboot returns to the installed ROM'),('CORE04','Recovery entry and stock rollback path'),('CORE05','Install/update preserves intended setup and app data'),('CORE06','User zero unlocks and app data becomes available'),('CORE07','Install and launch ordinary applications'),('CORE08','Application lifecycle, Home and task switching'),('CORE09','Internal app files read/write'),('CORE10','Android Keystore key generation and cryptographic round trip'),('CORE11','Screen lock/unlock without credentials'),('CORE12','PIN/password/pattern lock and credential unlock'),('CORE13','On-disk encryption of user data'),('CORE14','Application sandbox and runtime permissions'),('CORE15','SELinux enforcement and engineering exceptions documented'),('CORE16','Clock/date/timezone and RTC correctness'),('CORE17','Framework alarm scheduling and delivery'),('CORE18','Permission dialogs and permission management'),('CORE19','Recovery/public install usable on another SM-T110')],
'Display and controls':[
('INPUT01','Native display geometry/orientation'),('INPUT02','Applications and notifications draw correctly'),('INPUT03','Brightness and backlight control'),('INPUT04','Screen off/on and display wake'),('INPUT05','Single-finger touch and coordinate alignment'),('INPUT06','Multitouch'),('INPUT07','Physical Home'),('INPUT08','Physical Back'),('INPUT09','Physical Recents'),('INPUT10','Volume keys'),('INPUT11','Power key, sleep/wake and power menu'),('INPUT12','Hardware/onscreen navigation switch and mutual exclusion'),('INPUT13','Onscreen navigation buttons'),('INPUT14','Accelerometer-driven screen rotation'),('INPUT15','External USB keyboard/mouse')],
'Power and hardware monitoring':[
('POWER01','Battery level/status reported'),('POWER02','USB charging detected'),('POWER03','Wall charger and unplug/replug state'),('POWER04','Battery temperature/health reporting'),('POWER05','Deep suspend/idle and wake'),('POWER06','Off-mode charging behavior'),('POWER07','Normal shutdown'),('POWER08','Thermal monitoring and protection interface')],
'Audio and media':[
('AUDIO01','Speaker sound output'),('AUDIO02','Microphone recording'),('AUDIO03','Headphone output and jack detection'),('AUDIO04','Headset microphone/buttons where supported'),('AUDIO05','Media volume and mute'),('AUDIO06','Audio focus and application switching'),('AUDIO07','Music/audio file playback'),('AUDIO08','Alarm/notification audible output'),('AUDIO09','Video playback and audio/video sync'),('AUDIO10','Audio recording and media-file encoding')],
'Camera':[
('CAM01','Rear camera enumerated by Android'),('CAM02','Rear camera preview'),('CAM03','Still capture and saved JPEG'),('CAM04','Video recording and playback'),('CAM05','Camera orientation/rotation'),('CAM06','Supported camera controls and sensor capabilities'),('CAM07','Camera permission and use by another app'),('CAM08','Front camera/flash only if actually present')],
'Wi-Fi, networking and Bluetooth':[
('NET01','Wi-Fi driver/HAL/interface available'),('NET02','Wi-Fi enable/disable'),('NET03','Wi-Fi scan'),('NET04','Authenticate/connect to access point'),('NET05','DHCP, IP and default route'),('NET06','DNS and HTTPS internet access'),('NET07','Reconnect after sleep and reboot'),('NET08','Airplane mode and Wi-Fi override'),('NET09','Wi-Fi hotspot/tethering if hardware supports it'),('NET10','Bluetooth adapter/driver/HAL available'),('NET11','Bluetooth enable/disable and discovery'),('NET12','Bluetooth pairing'),('NET13','Bluetooth audio'),('NET14','Bluetooth file/HID/BLE profiles where supported'),('NET15','Network/VPN framework operation')],
'Location, sensors, storage and USB':[
('HW01','GNSS/GPS provider and position fix'),('HW02','Location permissions and provider settings'),('HW03','Accelerometer sensor enumerated and events delivered'),('HW04','Other physically fitted sensors'),('HW05','Vibration/haptics if fitted'),('HW06','Internal emulated/shared storage accessible to normal apps'),('HW07','MediaStore indexing and media picker'),('HW08','Files/DocumentsUI and Storage Access Framework'),('HW09','MicroSD detection, mounting and file read/write'),('HW10','USB OTG/storage if supported'),('HW11','USB ADB connection and transfers'),('HW12','USB MTP/file transfer'),('HW13','USB function selection and reconnect')],
'Android applications and standard services':[
('APP01','Launcher Home and app drawer'),('APP02','Settings opens and settings pages operate'),('APP03','Settings search and result navigation'),('APP04','Keyboard displays and text entry works'),('APP05','Clipboard copy/paste'),('APP06','Notification posting, shade, expansion and dismissal'),('APP07','Quick Settings tile actions'),('APP08','Clock/timer/alarm application'),('APP09','Browser/WebView renders local content and JavaScript'),('APP10','Widgets can be added and updated'),('APP11','Contacts/calendar local operation'),('APP12','Accessibility services and navigation'),('APP13','Screen capture/screenshot action'),('APP14','App settings and default-app selection'),('APP15','Backup/restore application behavior'),('APP16','Download manager and opening downloaded files')],
'Existing LineageOS functional integrations':[
('LOS01','Native Buttons settings and key customization'),('LOS02','Trust/security dashboard and alerts'),('LOS03','Native Wallpaper & style selection and Home/Lock application'),('LOS04','Status bar/Quick Settings configuration functions'),('LOS05','Profiles service and profile switching'),('LOS06','LiveDisplay/Night Light functions supported by this hardware'),('LOS07','AudioFX with real audio output'),('LOS08','Recorder with working microphone'),('LOS09','Privacy/permission controls'),('LOS10','Power-menu actions'),('LOS11','Native updater/manual update integration'),('LOS12','Accounts/synchronization where configured'),('LOS13','Developer options and ADB controls'),('LOS14','Supported gestures and hardware wake options')],
'Model and distribution boundaries':[
('SCOPE01','Cellular calls/SMS/mobile data on this Wi-Fi-only model'),('SCOPE02','NFC/fingerprint/IR and other absent hardware'),('SCOPE03','Google apps are optional and not falsely claimed included'),('SCOPE04','LineageOS20 capabilities distinguished from newer Android versions')],
}
items=[]
for group,entries in groups.items():
    for ident,title in entries:items.append({'id':ident,'group':group,'function':title,'status':'NOT_CHECKED','evidence':[],'note':''})
doc={'phase':'FUNCTIONAL_AUDIT_IN_PROGRESS_NO_FIXES_ALLOWED','build':'system v27 / BOOT v29','scope':'Operational functions of fitted hardware and existing Android13/LineageOS20 components; visual polish, speed tuning and new features are phase2','items':items,'nonfunctional_deferred':['UI performance/smoothness and animations except functional hangs','Layout/spacing/icon aesthetics','Higher-quality default wallpaper collection via native Lineage picker','Extra features and visual customization']}
path=e/'checklist.json'
assert not path.exists(),'Do not overwrite an in-progress audit'
path.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
text=['# Functional checklist — SM-T110 LineageOS20 / Android13','',
'Audit in progress. No fixes or ROM changes until this assessment is complete.',
'Only evidence-backed PASS items receive a tick. BLOCKED/UNVERIFIED are not passes.',
'Service declarations and installed packages alone do not prove operation.',
'Visual polish, smoothness, new features and HQ wallpapers are deferred to phase2.','']
for group,entries in groups.items():
    text+=['## '+group,'']+[f'- [ ] {ident}: {title} — NOT CHECKED' for ident,title in entries]+['']
(p/'FUNCTIONAL-CHECKLIST.md').write_text('\n'.join(text),encoding='utf-8')
print('FUNCTIONAL_INVENTORY_CREATED',len(items),'items')
