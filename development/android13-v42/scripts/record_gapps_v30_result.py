"""Record the measured v30 outcome, keeping the original audit immutable."""
from pathlib import Path
from collections import Counter
import hashlib,json
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41';q=e/'gapps-v30-test';a=p/'evidence/functional-audit-20261110'
install=json.loads((q/'installation.json').read_text());live=json.loads((q/'live-verification.json').read_text())
assert install['boot_id']==live['boot_and_server'][0] and live['boot_completed']=='1'
assert live['zram_started_without_manual_activation'] and live['google_core_packages_registered'] and live['old_data_profile_present']
assert live['unsupported_optional_keyboard_library_absent'] and live['getenforce']=='Enforcing'
result={'status':'BOOTED_GOOGLE_APPS_PRESENT_ZRAM_ACTIVE_STARTUP_UNSTABLE','system_version':'v30-gapps','boot_version':34,
 'system_sha256':install['system_sha256'],'boot_sha256':install['boot_sha256'],'boot_id':install['boot_id'],
 'system_server':install['system_server'],'boot_completed_observed_uptime_seconds':float(install['uptime'].split()[0]),
 'kernel_rebooted_during_qualification':False,'android_system_server_restarted':True,
 'startup_blocker':'TetheringService ANR; ActivityManager killed networkstack process, and ConnectivityModuleConnector restarted system_server. Other SystemUI startup ANRs also remain.',
 'native_keyboard':'Loaded unchanged libjni_latinime.so; incompatible optional Google gesture library omitted. No physical typing pass claimed.',
 'google_apps_registered':True,'google_signin_or_download_qualified':False,'wifi_still_unported':True,
 'zram_automatic':True,'zram_logical_bytes':536870912,'zram_activation_uptime_seconds':56.977172,
 'effective_swappiness':60,'effective_swap_page_cluster':0,'experimental_swappiness_100_denied_by_existing_proc_policy':True,
 'advanced_restart':'Lineage secure setting restored to1; native fallback menu showed only Power off/Restart during SystemUI ANR. Kernel alias is installed. No Recovery/Bootloader target qualified.',
 'physical_button_lights':'Capability review: no key-light node; adjacent-model non-backlit evidence only, exact hardware not confirmed.',
 'overall_lag_fixed':False,'physical_volume_function_pass_retained':True,'physical_typing_tested':False,
 'h264':'Still unqualified/failed on v29 userland; same codec builds in v30, no new pass claimed.',
 'aac':'Ordinary-app decode to memory passes, actual speaker/playback remains unported.',
 'old_profile_preserved':True,'physical_system_written':False,'recovery_unchanged':True,
 'functional_checklist_complete':False,'evidence':'evidence/offline-v41/gapps-v30-test'}
for dest in [q/'result.json',e/'result.json',p/'hardware-tests/LATEST-RESULT.json']:
    dest.write_text(json.dumps(result,indent=2)+'\n')
install['status']=result['status'];install['qualification']='result.json';(q/'installation.json').write_text(json.dumps(install,indent=2)+'\n')
baseline=(a/'baseline-before-fixes.json').read_bytes()
assert hashlib.sha256(baseline).hexdigest()=='64e408e92cb0f57f5047de49a9830d49a31624ed45be5845823e2e75996ec62a'
d=json.loads((a/'checklist.json').read_text());d['build']='v30-GApps / BOOT34, booted with registered Google apps and automatic zram; startup remains unstable'
updates={
 'CORE02':('FAIL','System v30 boots after networkstack/TetheringService startup ANR and system_server restart (305 -> 1146); SystemUI also shows startup ANRs. Boot completed observed395.05s. RAM swap activated automatically at56.977s, but does not fix startup by itself.','startup-restart.txt'),
 'LOS10':('PARTIAL','Advanced restart setting restored to1. Power menu reached during SystemUI instability offers only Power off/Restart. BOOT34 retains Samsung bootloader->download target mapping; native advanced menu and target execution are unqualified.','settled-ui.png'),
 'SCOPE03':('PASS','MindTheGapps remains optional. Owner requested private ARM32 Android13 installation. Google core APKs register on v30; online use unqualified. Optional Google gesture library omitted due proven Cortex-A9 SIGILL; native Lineage keyboard preserved.','live-verification.json'),
}
for i in d['items']:
    if i['id'] in updates:
        status,note,file=updates[i['id']];i.update(status=status,note=note,evidence=['../offline-v41/gapps-v30-test/'+file])
    if i['id']=='INPUT10':i['note']+=' Owner reports severe response lag; working key mapping does not establish UI latency.'
extra=[
 ('GAPPS01','Google apps installation','PASS','Play Store, Google Play services and Google Services Framework registered on the installed ARM13 build.','live-verification.json'),
 ('GAPPS02','Google first setup and online Play Store','BLOCKED','Setup wizard reaches welcome. Google sign-in and app downloads require working networking and owner setup. No account actions taken.','settled-ui.png'),
 ('LIGHT01','Capacitive Back/Recents key illumination','CAPABILITY_REVIEW','No fitted LED control verified. Keep separate from the passing panel brightness control.','../button-light-capability.md'),
]
for ident,title,status,note,file in extra:
    if not any(i['id']==ident for i in d['items']):d['items'].append({'id':ident,'group':'Additional owner requests','function':title,'status':status,'note':note,'evidence':['../offline-v41/gapps-v30-test/'+file]})
d['summary']=dict(Counter(i['status'] for i in d['items']));d['repair_progress']='See evidence/offline-v41/gapps-v30-test/result.json. Baseline and earlier owner verification retained.'
(a/'checklist.json').write_text(json.dumps(d,indent=2)+'\n');assert (a/'baseline-before-fixes.json').read_bytes()==baseline
lines=['# Functional checklist - SM-T110 / LineageOS20','','Original baseline is frozen. Only confirmed working functions are ticked.','','Counts: '+', '.join(f'{k}={v}' for k,v in d['summary'].items())+'.','','[Current v30 result](evidence/offline-v41/gapps-v30-test/result.json). [Frozen baseline](evidence/functional-audit-20261110/baseline-before-fixes.json).','']
group=None
for i in d['items']:
    if group!=i['group']:group=i['group'];lines+=['## '+group,'']
    links=', '.join('[evidence](evidence/functional-audit-20261110/'+s+')' for s in i['evidence'])
    lines.append(f'- [{"x" if i["status"]=="PASS" else " "}] **{i["id"]} {i["function"]} - {i["status"]}**. {i["note"]} {links}')
(p/'FUNCTIONAL-CHECKLIST.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(p/'CURRENT-STATUS.md').write_text('''# Current state - 2026-11-11

Installed v30-GApps / BOOT34; read evidence/offline-v41/gapps-v30-test/result.json.
Verified read-only 2047MiB loop image SHA143c7a27936f4ad48a2ef8311bd9e78e64499ecbec28777ef9fdfa427526758c.
BOOT SHA013b70666b9110c5320396503c0377600352febf6053b628f13c07e150cac590.
Boot b1295dec-7878-469f-ac9e-1ff4420f90d0, system_server1146 after initial305
restarted. Boot completed observed at395.05s. Still an engineering build.
No additional reboot, package modification or account action pending.

Confirmed: native RAM-only zram starts at56.977s, 512MiB logical, enforcing;
correct swap_block_device label and old kernel's scoped init swapon permission.
The experimental swappiness100 write is denied; actual60, page-cluster0.
Do not broaden generic proc write permissions for an unmeasured tuning benefit.
ARM13 MindTheGapps installed and Play Store/Play services/GSF registered. Native
keyboard library loaded; optional Google gesture JNI omitted because SDIV at
+0x61520 SIGILLs on Cortex-A9. All Google APKs and native Lineage apps retained.
Wi-Fi remains unported, Google setup/sign-in/downloads are not qualified.

Startup still fails: TetheringService startup ANR kills networkstack, triggering
ConnectivityModuleConnector's system_server restart. Other SystemUI ANRs and
software-rendering/I/O pressure remain. Prior v29 watchdog and codec evidence
are in gapps-v29-test/FINDINGS.md. AAC to buffers passes; H264 userland still
fails and cannot be called fixed. Original kernel ION overrun fixed by0081.

Advanced restart restored to1; fallback power menu lacks the advanced entries
when SystemUI is unresponsive. Samsung bootloader->download alias built, target
not physically verified. Don't select plain Restart as a test of the submenu.
Key lighting remains a capability review (see button-light-capability.md).
Native hardware navigation stays selected (force_show_navbar0); INPUT10/11
owner functional passes retained. Latency remains unresolved.

Both Android data profiles preserved. Original setup is the pre-gapps profile.
Rollback host system28/BOOT32 and unchanged TWRP remain. NEVER write physical
SYSTEM/mmcblk0p15. Only guarded loop-image updates, with matched preload policy.
Build SSD E, T110Build:/root/t110-build/{lineage20,out-system}, remains usable.
Kernel build Ubuntu:/root/t110-build/{kernel-display-i2c,out-display-i2c}.

Kernel contribution: https://github.com/visyone/android_kernel_samsung_goya/pull/2
No Google binaries or private device data published. Functional checklist remains
open; keep native features and defer release/polish until qualification.
''',encoding='utf-8')
(p/'RESUME-NEXT.md').write_text('''# Resume next - v30-GApps / BOOT34 installed

Use CURRENT-STATUS.md and evidence/offline-v41/gapps-v30-test/result.json.
Do not repeat incremental full boots. Current pair is installed and verified;
both inner profiles and the v28/BOOT32 rollback remain. Never write SYSTEM.

Focus next offline pass on real startup/latency evidence. Read startup-restart.txt,
tethering-startup-anr.txt and early-service-anr.txt. Tethering main had recovered
to idle by dump time; the ANR is proven, a permanent deadlock is not. Actual
ART dump shows NetworkStack.odex is verify-only and TetheringNext is extract,
on a device with no JIT. The existing0042 flattened-APEX preopt selects only
com.android.permission. Extend that native build path to precompile the exact
TetheringNext APEX and installed NetworkStack while retaining PermissionController;
verify real oat paths, classloader checksums and compiler filters before a boot.
Do not disable the watchdog, strip Google apps, or inflate timeouts as a substitute.

Advanced restart: native SystemUI path honors Lineage secure advanced_reboot;
LegacyGlobalActions fallback only creates RestartAction, no submenu. Confirm the
actual provider and stable main UI before claiming it fixed. If fallback must
support advanced targets, preserve the same primary-user/secure-keyguard guard
and native reboot reason. Kernel alias bootloader->download already installed.

After stable setup, check real volume response and keyboard typing, Wi-Fi and
online Google behavior. Keep hardware-button LED capability separate from touch
mapping and the working panel. Existing open work includes H264 userspace,
camera, radios, real audio, sensors/GNSS, accessories, and later feature/polish.
''',encoding='utf-8')
print('CURRENT_V30_RECORDED',d['summary'])
