"""Record observed repair results without promoting unqualified functions."""
from pathlib import Path
from collections import Counter
import hashlib,json
p=Path(__file__).resolve().parents[1];e=p/'evidence/offline-v41';audit=p/'evidence/functional-audit-20261110'
install=json.loads((e/'installation.json').read_text());live=json.loads((e/'live-verification.json').read_text())
assert install['boot_id']==live['boot'] and live['system_server']==live['post_system_server']=='309'
assert live['framework_capture']['framebuffer_mean_absolute_difference']==[0.0,0.0,0.0]
assert live['native_brightness']==[{'setting':40,'panel':40},{'setting':220,'panel':220}]
live['framework_capture']['visual_review_pending']=False
live['framework_capture']['visual_review']='Three valid captures show real Settings and the current SystemUI ANR dialog, with no pixel corruption. Exact framebuffer match; dialog itself remains a startup failure.'
(e/'live-verification.json').write_text(json.dumps(live,indent=2)+'\n')
result={'status':'BOOTED_STARTUP_ANR_CODEC_TEST_USB_DISCONNECTED','system_version':28,'boot_version':31,'boot_id':live['boot'],'system_server':live['system_server'],'system_sha256':install['system_sha256'],'boot_sha256':install['boot_sha256'],'agent_boot_requests':1,'boot_completed':True,'full_boot_passed':False,'functional_checklist_complete':False,'ui_features_phase_started':False,'capture_pixels_qualified':True,'native_brightness_qualified':True,'startup_anr_free':False,'boot_animation_exit_uptime_ms':225451,'codec_status':'First normal-UID H264 decode began; USB disappeared before result. Neither successful decode nor a kernel panic is established. Await owner screen observation and saved logs.','device_current_state':'USB absent after decoder initialization; no additional reboot or flash requested','data_preserved':True,'recovery_unchanged':True,'host_rollback_system':27,'host_rollback_boot':29,'feature_requests':'FEATURE-BACKLOG.md','temporary_screen_preferences_restored':live['temporary_settings_restored'],'qa_package_cleanup_pending_usb':True}
(e/'result.json').write_text(json.dumps(result,indent=2)+'\n')
(p/'hardware-tests/LATEST-RESULT.json').write_text(json.dumps({**result,'evidence':'evidence/offline-v41'},indent=2)+'\n')
pairpath=p/'artifacts/lineage20-rom-v28/rom-pair.json';pair=json.loads(pairpath.read_text());pair.update(status=result['status'],full_boot_passed=False,boot_id=live['boot'],functional_checklist_complete=False,capture_pixels_qualified=True,native_brightness_qualified=True);pairpath.write_text(json.dumps(pair,indent=2)+'\n')
baseline=(audit/'baseline-before-fixes.json').read_bytes();d=json.loads((audit/'checklist.json').read_text());d['build']='system v28 / BOOT v31; single combined test, startup ANRs and interrupted codec test remain';d['repair_progress']='See evidence/offline-v41/result.json; do not rerun the immutable baseline or call this a fully working ROM.'
updates={
    'CORE02':{'status':'FAIL','evidence':['../offline-v41/startup-late.txt','../offline-v41/boot-crash.txt','../offline-v41/installed-screencap-0.png'],'note':'The built optional-HAL nonretry fix is installed and IMMS phase550 now completes in3.594s, but the whole boot is not fixed: SystemUI/keyguard and fused-location ANRs, early ueventd SIGSEGV/restart, boot-animation exit225.451s. No system_server restart observed through display/brightness checks.'},
    'CORE16':{'status':'PARTIAL','evidence':['../offline-v41/live-verification.json','../offline-v41/boot-clock.txt'],'note':'Asia/Jerusalem persisted, but clock/RTC boot persistence failed: device was about42.8minutes behind host after reboot. Prior runtime correction did not establish persistence or network time.'},
    'INPUT03':{'status':'PASS','evidence':['../offline-v41/live-verification.json','../offline-v41/boot-lights.txt'],'note':'Installed normal Android lights service and device adapter; Android screen_brightness40/220 drove the actual panel node40/220, then restored original brightness/mode. No direct panel-write workaround used for this qualification.'},
    'APP13':{'status':'PARTIAL','evidence':['../offline-v41/live-verification.json','../offline-v41/installed-screencap-0.png','../offline-v41/installed-real-framebuffer.png'],'note':'Normal installed screencap saved three valid600x1024 PNGs, visually correct and exact framebuffer pixel match. Native SystemUI screenshot action/save path still pending; no screenrecord pass inferred.'},
}
for item in d['items']:
    if item['id'] in updates:item.update(updates[item['id']])
d['summary']=dict(Counter(i['status'] for i in d['items']));(audit/'checklist.json').write_text(json.dumps(d,indent=2)+'\n')
assert (audit/'baseline-before-fixes.json').read_bytes()==baseline
lines=['# Functional checklist — SM-T110 / LineageOS20','','Automatic assessment completed before repairs; the immutable baseline is retained.','Functional repairs remain in progress. UI/performance/features/HQ wallpapers wait until functional completion.','Only PASS is ticked. Native images and built patches alone are not functional passes.','','Counts: '+', '.join(f'{k}={v}' for k,v in d['summary'].items())+'.','','Current installed pair: system v28 / BOOT v31. [Latest result](evidence/offline-v41/result.json).','[Baseline](evidence/functional-audit-20261110/baseline-before-fixes.json). [New feature requests](FEATURE-BACKLOG.md).','']
group=None
for item in d['items']:
    if group!=item['group']:group=item['group'];lines+=['## '+group,'']
    links=', '.join('[evidence](evidence/functional-audit-20261110/'+v+')' for v in item['evidence'])
    lines.append(f'- [{"x" if item["status"]=="PASS" else " "}] **{item["id"]} {item["function"]} — {item["status"]}**. {item["note"]} {links}')
(p/'FUNCTIONAL-CHECKLIST.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'baseline_sha256':hashlib.sha256(baseline).hexdigest(),'summary':d['summary'],'result':result['status']},indent=2))
