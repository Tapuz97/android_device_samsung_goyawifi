from pathlib import Path
import json
p=Path(__file__).resolve().parents[1]
script=(p/'scripts/verify_v19_contents.py').read_text()
script=script.replace('lineage20-rom-v18','lineage20-rom-v19').replace('lineage20-rom-v19','lineage20-rom-v20',1)
# The first replacement affected old-image reference, so set it explicitly.
script=script.replace("old=b/'export-lineage20-rom-v19/system.raw.img'","old=b/'export-lineage20-rom-v19/system.raw.img'")
script=script.replace('offline-v29','offline-v30').replace('ORIENTATION_270','ORIENTATION_0')
script=script.replace("'system/lib/libcodec2_vndk.so','system/lib/libEGL.so','system/lib/libui.so',", "'system/bin/surfaceflinger','system/vendor/lib/libhwc2onfbadapter.so',\n             'system/lib/libcodec2_vndk.so','system/lib/libEGL.so','system/lib/libui.so',")
script=script.replace("for name in ['system/bin/surfaceflinger','system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service',\n             'system/vendor/lib/libhwc2onfbadapter.so']:","for name in ['system/vendor/bin/hw/android.hardware.graphics.composer@2.1-service']:")
script=script.replace("assert b'T110 framebuffer power: %s' in composer", "assert b'final panel rotation=270' in composer\nassert b'T110 framebuffer power: %s' in composer")
script=script.replace('0054-composer-t110-scanout-and-display-power.patch','0055-composer-t110-natural-portrait-scanout.patch')
script=script.replace('v19 contents','v20 contents')
assert "export=b/'export-lineage20-rom-v20'" in script and "old=b/'export-lineage20-rom-v19/system.raw.img'" in script
(p/'scripts/verify_v20_contents.py').write_text(script)
script=(p/'scripts/finalize_v19_offline.py').read_text().replace('v19','v20').replace('offline-v29','offline-v30').replace('20261107T120143Z','20261107T124134Z')
script=script.replace("'Natural portrait panel orientation matching stock270',\n           'EGL window projection flip applied after display rotation',", "'HWC exposes natural600x1024 with no second rotation in SurfaceFlinger',\n           'Bounds-checked final-frame rotation270 matching stock panel mounting',")
(p/'scripts/finalize_v20_offline.py').write_text(script)
script=(p/'scripts/stage_v19_system.py').read_text().replace('v19','v20').replace('offline-v29','offline-v30')
(p/'scripts/stage_v20_system.py').write_text(script)
trial=p/'hardware-tests/20261107-141828-core'
observation=json.loads((trial/'stability-observation.json').read_text())
state=(trial/'final-v19-state.txt').read_text()
assert 'RUNNING_UNLOCKED' in state and (trial/'final-v19-crash.txt').stat().st_size==0
result=dict(status='STARTUP_STABLE_PORTRAIT_COMPOSITION_FAILED',hardware_tested=True,hardware_validated=False,
    full_boot_passed=False,boot_completed=True,user_unlocked=True,system_server_pid=364,
    final_uptime_seconds=float(state.split()[0]),stability=observation,
    logical_display=[600,1024],physical_framebuffer=[1024,600],user_report='Blank screen with white stripes at panel top',
    framebuffer_capture='v19-settled-page-0.png',screen_power_ioctl_succeeded=True,touch_validated=False,
    offscreen_gpu_roundtrip='Both1024x600 and600x1024 succeeded, including textured quarter-turn; no framebuffer writes',
    caveat='GPU test checks the buffer/texture path, not complete HWUI or RenderEngine composition',
    next='v20 moves fixed panel rotation into final CPU scanout, retaining source portrait and existing startup fixes')
(trial/'result.json').write_text(json.dumps(result,indent=2)+'\n')
pair_path=p/'artifacts/lineage20-rom-v19/rom-pair.json';pair=json.loads(pair_path.read_text())
for k in ['status','hardware_tested','hardware_validated','full_boot_passed','boot_completed']:pair[k]=result[k]
pair['hardware_trial']=str(trial.relative_to(p));pair_path.write_text(json.dumps(pair,indent=2)+'\n')
entry='''## v20 BUILD ACTIVE; v19 PORTRAIT FRAME FAILED - 2026-11-07 14:42

Only build50738 is active, system-image-20261107T124134Z.log in T110Build. Shell53621 keeps distro alive. v19 trial hardware-tests/20261107-141828-core finished360sec stability with same system_server364, user unlocked and crash buffer empty, but user/photo confirm white stripes and black app area. result.json and v19 rom-pair.json mark UI failure. Offscreen t110_portrait_roundtrip verified both source sizes and texture rotation, no fb0/display writes. Its hint7 variation was never queried by the blob, so it does NOT validate or implicate pre-rotation. SurfaceFlinger dump stride2816 is actually getUsage() due an upstream dump-label bug; do NOT diagnose it as buffer stride. Actual600px allocation stride608 is correct. Native screencap again returned no PNG. Settings launch stayed in SetupWizard; no Settings rendering evidence.

v30 source changes apply fixed stock270 panel rotation in T110Framebuffer scanout, exposing600x1024 directly to Android with primary orientation0. All-pixel bounds/stride/padding/page/channel-order tests pass underASan/UBSan. Cumulative0055 supersedes0054; renderer0053 retained (at orientation0 equivalent to working v18 projection). No input double rotation. Actual display usability still unverified. Currentboot ended intentionally with hash-verified t110_full_return_to_recovery at14:42; ADB disconnect exit1 expected, verify recovery before stage. No stock rollback. Do not start another boot until build/contents checks pass.

Prepared verify_v20_contents.py, finalize_v20_offline.py, stage_v20_system.py. After build50738 success: archive_graphics_system.sh lineage20-rom-v20 system-image-20261107T124134Z.log; verify actual contents; finalize locally; stage checked compressed transfer in TWRP; immediately boot with unchanged v27 BOOT and --reuse-boot --stability-seconds360 using manifest hashes. Standing automatic-flash authorization, no approval/readiness summaries. Tablet user nearby. Latest user photo shows the exact captured white stripes at top.

'''
status=p/'CURRENT-STATUS.md';status.write_text(entry+status.read_text(encoding='utf-8'),encoding='utf-8')
print('V20_POST_BUILD_TOOLS_PREPARED')
