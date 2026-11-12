"""Refresh current entry points without rewriting the frozen functional baseline."""
from pathlib import Path
from collections import Counter
import hashlib,json,datetime
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41';audit=p/'evidence/functional-audit-20261110'
baseline=(audit/'baseline-before-fixes.json').read_bytes()
assert hashlib.sha256(baseline).hexdigest()=='64e408e92cb0f57f5047de49a9830d49a31624ed45be5845823e2e75996ec62a'
install=json.loads((e/'gapps-v29-test/installation.json').read_text())
report=json.loads((e/'boot32-test/app-api-report.json').read_text());assert report['completed']
assert all(i['status']=='PASS' for i in report['results'] if i['id'] in ['aac-software-decode','aac-omx-decode'])
owner={'reported_at':datetime.datetime.now().astimezone().isoformat(),'reports':['Volume keys and OS severely laggy, improved relative to previous builds','Advanced restart enabled but not working','Physical Recents/Back key backlights do not work'],'requested_addition':'Official ARM32 Android13 MindTheGapps / Play Store / Google apps','advanced_restart_failure_detail_pending':True,'stock_keylight_history_pending':True,'keep_native_lineage_features':True}
(e/'owner-followup-20261110.json').write_text(json.dumps(owner,indent=2)+'\n')
old=e/'result.json';history=e/'boot31-result-history.json'
if not history.exists():history.write_bytes(old.read_bytes())
result={'status':install['status'],'installation_record':'gapps-v29-test/installation.json',
 'previous_qualified_boot':{'system':28,'boot':32,'boot_id':'046c74cc-c706-4b07-8105-bd06c5818ffe','system_server':'304','startup_animation_exit_ms':217826,'startup_anr_free':False,'kernel_codec_crash_reproduced_after_fix':False,'aac_buffer_decode':'PASS both C2/OMX API names','h264_decode':'FAIL missing gralloc in isolated codec APEX','qa_uninstalled':True,'zram':'Did not start; missing max_comp_streams node'},
 'new_pair':{'system':'v29-gapps','boot':33,'offline_verified':True,'hardware_validation_pending':True,'system_sha256':install['system_sha256'],'boot_sha256':install['boot_sha256']},
 'kernel_fault_proven':'Saved SYSTEM_LAST_KMSG: mm/memory.c:2202 via ion_system_heap_map_user overran decoder VMA',
 'new_fixes':['0082 codec isolated APEX permitted absolute libhardware lookup','0083 explicit legacy swapon permission and max_comp_streams=-1','0084 standard YV12 raw lock fallback','0085 bootloader alias to Samsung download'],
 'kernel_contribution':'https://github.com/visyone/android_kernel_samsung_goya/pull/2',
 'functional_checklist_complete':False,'performance_fixed':False,'recovery_unchanged':True,'physical_system_written':False,
 'gapps_requires_fresh_profile':True,'prior_setup_preserved':'/data/local/tmp/t110-rom-data.pre-gapps'}
old.write_text(json.dumps(result,indent=2)+'\n');(p/'hardware-tests/LATEST-RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
d=json.loads((audit/'checklist.json').read_text());d['build']='v29-GApps / BOOT33 installation in progress; see live installation record'
updates={
'CORE02':{'status':'FAIL','note':'Last qualified BOOT32 reached Android with stable system_server304, but SystemUI restarted during startup ANRs; animation exit217.826s. Zram failed because old kernel lacks max_comp_streams. BOOT33 corrects the control and legacy swap permission; new combined test pending.','evidence':['../offline-v41/boot32-test','../offline-v41/gapps-v29-test/installation.json']},
'AUDIO07':{'status':'PARTIAL','note':'BOOT32 normal-app AAC decoder succeeds through C2 and explicit OMX API names:47 output buffers/96256 bytes each. This is decode to memory only; speaker/audio HAL and actual playback remain unported. H264 failed separately in isolated gralloc loading.','evidence':['../offline-v41/boot32-test/app-api-report.json']},
'LOS10':{'status':'PARTIAL','note':'Owner reports advanced restart does not work despite native Lineage Secure advanced_reboot=1. Exact menu/target failure detail pending. BOOT33 accepts Android bootloader as Samsung download; recovery helper already works, submenu and native target actions remain to qualify.','evidence':['../offline-v41/owner-followup-20261110.json','../offline-v41/reboot-alias-source.json']},
'SCOPE03':{'status':'PASS','note':'Google apps remain optional. Owner explicitly requested official MindTheGapps ARM32 Android13; full package is verified and privately integrated into v29 loop image. Actual installed/runtime/online Play Store qualification tracked separately, not falsely claimed working.','evidence':['../offline-v41/gapps-v29-offline-verification.json','../offline-v41/mindthegapps-signature.json']}}
for i in d['items']:
    if i['id'] in updates:i.update(updates[i['id']])
d['summary']=dict(Counter(i['status'] for i in d['items']));d['repair_progress']='See offline-v41/result.json and gapps-v29-test/installation.json. Do not rerun frozen baseline.'
(audit/'checklist.json').write_text(json.dumps(d,indent=2)+'\n');assert (audit/'baseline-before-fixes.json').read_bytes()==baseline
lines=['# Functional checklist - SM-T110 / LineageOS20','','Original automatic audit is frozen; only verified working items are ticked. Functional work remains incomplete.','','Counts: '+', '.join(f'{k}={v}' for k,v in d['summary'].items())+'.','','[Live installation](evidence/offline-v41/gapps-v29-test/installation.json). [Latest findings](evidence/offline-v41/result.json). [Frozen baseline](evidence/functional-audit-20261110/baseline-before-fixes.json).','']
group=None
for i in d['items']:
    if group!=i['group']:group=i['group'];lines+=['## '+group,'']
    links=', '.join('[evidence](evidence/functional-audit-20261110/'+s+')' for s in i['evidence'])
    lines.append(f'- [{"x" if i["status"]=="PASS" else " "}] **{i["id"]} {i["function"]} - {i["status"]}**. {i["note"]} {links}')
(p/'FUNCTIONAL-CHECKLIST.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(p/'CURRENT-STATUS.md').write_text('''# Current state - 2026-11-10

Read evidence/offline-v41/gapps-v29-test/installation.json first for the live install/boot state.
System v29-GApps and BOOT33 passed offline verification. Installation was started
automatically under standing owner authorization. Never infer completion from this file.

Previous live pair v28/BOOT32 reached Android (boot046c74cc-c706-4b07-8105-bd06c5818ffe,
system_server304). ION VMA overrun caused the earlier v31 crash, proven by saved
SYSTEM_LAST_KMSG.0081 fixes it;37,414 extracted-production host cases pass and
the v32 app codec test no longer reboots. AAC decode passes both API names;
H264 still failed loading gralloc.0082 loader and0084 standard YV12 raw lock
fallback are compiled in new system29, with same-boot isolated native probes passed.

Startup/performance remain failed. BOOT32 animation exit217.826s and SystemUI
startup ANRs. Its zram did not activate because the old kernel lacks
max_comp_streams; next fstab uses -1 to skip that control. New system policy0083
retains old kernel file:swapon permission, explicitly only for init/ram_device.
BOOT33 preserves touch/config/galcore and adds0085 bootloader->download reason.
Only real hardware target tests can qualify it. Advanced-menu behavior detail pending.

Official MindTheGapps13 ARM20231025 full payload is privately integrated; its
JAR signature and publisher/OTA certificates match. The loop image is2047MiB,
larger than physical SYSTEM by design. NEVER flash it to mmcblk0p15. Use only
the guarded loop installer. BOOT33 supports both original and Google geometries.
Fresh Android data is required; existing setup is retained as pre-gapps profile.
No owner Google account actions, sign-in or account terms are authorized.

Host rollback: system28/BOOT32 plus preserved old profile; recovery is unchanged.
Installer removes only independently host-backed obsolete generated device images.
E full build and latest kernel build passed; no new disk retries during this work.
Full source T110Build:/root/t110-build/lineage20, OUT_DIR=/root/t110-build/out-system.
Kernel Ubuntu:/root/t110-build/kernel-display-i2c, out-display-i2c.

Camera, Wi-Fi/Bluetooth, native audio, sensors/GNSS and accessories still need
porting/qualification. Owner reports severe lag and key backlights absent.
No button LED controls in current kernel/sysfs; original hardware capability
pending confirmation. Standard panel brightness remains qualified separately.
Functional checklist frozen baseline is unchanged; owner INPUT10/11 PASS retained.
Keep native Lineage features, wallpapers/settings and hardware/software-nav toggle.
DT2W and native Recents Clear all/icon are in FEATURE-BACKLOG.md for later.

Kernel contribution submitted separately: https://github.com/visyone/android_kernel_samsung_goya/pull/2
Do not publish private device logs/IDs, Google binaries or claim the ROM release-ready.
''',encoding='utf-8')
(p/'RESUME-NEXT.md').write_text('''# Resume next

Start with CURRENT-STATUS.md, evidence/offline-v41/result.json and the live
gapps-v29-test/installation.json. A single combined install/boot is in progress.
Do not start a duplicate test or assume a build means it booted. Capture current
boot identity, kernel log, crash buffers and startup ANRs before modifying anything.

New pair system29-GApps / BOOT33 includes codec loader+YV12 fixes, legacy zram
permission/control and Samsung bootloader alias. Check actual /proc/swaps and
decoder outputs; do not report inference as functional success. Google APKs
presence is not online Play Store sign-in/download qualification (Wi-Fi unported).
Preserve the pre-gapps inner profile; no physical userdata factory format.

If the installer stopped, inspect its exact recorded stage before any recovery.
Rollback uses verified host system28/BOOT32 and the retained pre-gapps profile.
Physical SYSTEM has a read fault; NEVER write it. Untouched TWRP is the recovery path.
Do not run old hardcoded v28/v31 exporters/installers against this larger loop image.
Current source/build locations and hashes are in CURRENT-STATUS and provenance.

Owner volume/OS lag, advanced restart failure and button backlight report are in
owner-followup-20261110.json. Two text clarifications were requested; do not repeat.
Check pending replies. Advanced restart uses native Lineage secure setting.
Real navigation works; button LEDs may not be fitted. No arbitrary GPIO writes.
All native Lineage functionality must remain; functional work precedes polish.
''',encoding='utf-8')
contrib=p/'community/PENDING-FUNCTIONAL-CONTRIBUTIONS.md';text=contrib.read_text();start=text.index('- **Goya ION_IOC_MAP:');end=text.index('- **Optional Lineage HAL',start)
text=text[:start]+'''- **Goya ION mapping - submitted:** [upstream PR2](https://github.com/visyone/android_kernel_samsung_goya/pull/2)
  contains0079 MAP alias and0081 bounded SG/VMA mappings, plus the extracted
  production test (37,414 cases). Saved crash log proves the original overrun;
  installed BOOT32 no longer crashes during codec initialization, AAC passes.
  H264 still requires the separate userspace loader/YV12 fixes. Public PR excludes
  raw logs/IDs and makes no whole-ROM or H264 success claim. Existing shared-I2C
  PR is separate. Preparation/publication receipts in community/ion-map-bounds.
'''+text[end:];contrib.write_text(text,encoding='utf-8')
print('CHECKPOINT_UPDATED_BASELINE_UNCHANGED',d['summary'])
