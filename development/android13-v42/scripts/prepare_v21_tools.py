from pathlib import Path
import json
p=Path(__file__).resolve().parents[1]
s=(p/'scripts/verify_v20_contents.py').read_text().replace('v20 contents','v21 contents')
s=s.replace("export=b/'export-lineage20-rom-v20'","export=b/'export-lineage20-rom-v21'")
s=s.replace("old=b/'export-lineage20-rom-v19/system.raw.img'","old=b/'export-lineage20-rom-v20/system.raw.img'")
s=s.replace('artifacts/lineage20-rom-v19/','artifacts/lineage20-rom-v20/').replace('offline-v30','offline-v31').replace('0055-composer-t110-natural-portrait-scanout.patch','0056-composer-t110-padded-portrait-scanout.patch')
(p/'scripts/verify_v21_contents.py').write_text(s)
s=(p/'scripts/finalize_v20_offline.py').read_text().replace('v20','v21').replace('offline-v30','offline-v31').replace('20261107T124134Z','20261107T130215Z')
s=s.replace("'Bounds-checked final-frame rotation270 matching stock panel mounting',","'Bounds-checked final-frame rotation270 matching stock panel mounting',\n           'Accept actual608px padded backing for600px logical rows',")
(p/'scripts/finalize_v21_offline.py').write_text(s)
s=(p/'scripts/stage_v20_system.py').read_text().replace('v20','v21').replace('offline-v30','offline-v31');(p/'scripts/stage_v21_system.py').write_text(s)
trial=p/'hardware-tests/20261107-145659-core';state=(trial/'v20-failed-display-state.txt').read_text();assert 'RUNNING_UNLOCKED' in state
result=dict(status='STARTUP_UNLOCKED_SCANOUT_REJECTED_PADDED_BUFFER',hardware_tested=True,hardware_validated=False,full_boot_passed=False,boot_completed=True,user_unlocked=True,system_server_pid=365,observed_uptime_seconds=float(state.split()[0]),crash_buffer_empty=(trial/'v20-failed-display-crash.txt').stat().st_size==0,
    frame_count=0,scanout_error=-22,measured_logical_width=600,measured_padded_width=608,
    diagnosis='New adapter required private_handle paddedwidth==logical600. Real buffer reports608 in bothwidth andstride; changed guard to accept sufficient padded backing.',
    recovery_requested=True,additional_diagnostic_boots=0,
    evidence=['v20-early-sf.txt','portrait-output-roundtrip.txt'],touch_validated=False)
(trial/'result.json').write_text(json.dumps(result,indent=2)+'\n')
path=p/'artifacts/lineage20-rom-v20/rom-pair.json';pair=json.loads(path.read_text())
for key in ['status','hardware_tested','hardware_validated','full_boot_passed','boot_completed']:pair[key]=result[key]
pair['hardware_trial']=str(trial.relative_to(p));path.write_text(json.dumps(pair,indent=2)+'\n')
entry='''## v21 PADDING FIX BUILD ACTIVE - 2026-11-07 15:03

Only build54319 active, logsystem-image-20261107T130215Z.log inT110Build. v20 trial17258/hardware-tests/20261107-145659-core reachedboot_completed and userunlocked withsystem_server365/no fatalcrash, butcomposerframes0/error-22. Exactnewwidth equality check wrongly rejected private_handle width608 whilelogicalwidth600. Offscreenportrait-output-roundtrip measuredwords13=608,16=608,height1024,bytes0x260000,flags0x80000b03; renderedall16expectedcolorsfine. Correctedsource helper validPortraitAllocation accepts paddedwidth>=600 and proves backingbytecount; productionheaderfixture test fromactualpacket andfullpixelrotation/bounds ASan/UBSan PASS. 0056 supersedes0055. No property/input/kernel/startup changes. CPUrotationremains270, primaryorientation0. Guardedreturnhelper requestedTWRP at15:02; runner17258 willdetectrecoveryandfinish, verify beforestage. No morebootuntilcorrectedimageverified. No physicalUIclaim.

Preparedverify_v21_contents.py,finalize_v21_offline.py,stage_v21_system.py. After54319success archive lineage20-rom-v21 system-image-20261107T130215Z.log; verifycontents; finalize; stage; immediatelyonefullbootunchangedv27BOOT with--reuse-boot --stability-seconds180 andnewmanifestMD5. Standingautomaticflashauthorization. Needensureactualfirstframepannedbeforeaskuserportrait/touch. Existingv20imageMD5f888056ed7b2a736823ca378461a4a2f; existingBOOT942182cefec3cb7666096499220789d0,recoverycd9793e1ee8f284c9056b225885b5b1a. Evidencev31. Do not rerunone-timesourcefixscripts.

'''
path=p/'CURRENT-STATUS.md';path.write_text(entry+path.read_text(encoding='utf-8'),encoding='utf-8')
print('V21_TOOLS_PREPARED')
