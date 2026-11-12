from pathlib import Path
import json,datetime
p=Path(__file__).resolve().parents[1];trial=p/'hardware-tests/20261107-151636-core'
pairfile=p/'artifacts/lineage20-rom-v21/rom-pair.json';pair=json.loads(pairfile.read_text())
pair.update(status='BOOTS_AND_UNLOCKS_DISPLAY_CORRUPTION',hardware_tested=True,hardware_validated=False,full_boot_passed=False,
    trial=str(trial.relative_to(p)),physical_observations=['Full boot animation visible','Welcome corrupt with white bars','User reports touch responds','Recents No recent items displays correctly'],
    limits=['Welcome screen remains unusable; complete display validation failed','Wi-Fi radio and other unported hardware remain incomplete'])
pairfile.write_text(json.dumps(pair,indent=2)+'\n')
report=dict(boot_completed=True,user_unlocked=True,usable_ui_validated=False,stock_rollback_performed=False,
    system_server_pid='354',stability_observation=json.loads((trial/'stability-observation.json').read_text()),
    same_boot_graphics_checks={'software_canvas':'Correct full portrait image',
      'gpu_canvas_readback':'Correct 600x1024 and 1024x600 offscreen frames',
      'gpu_direct_surface':'Correct quadrants with CPU-readable backing; GPU-only backing had small black corner artifact',
      'recents':'Correctly rendered, user confirmed and framebuffer captured',
      'welcome':'Corruption/stale image persists; no usable screen claim'},
    temporary_property='debug.hwui.use_partial_updates was tested false, then restored to default behavior true; no reboot',
    app_crash='SetupWizard EGL_BAD_ACCESS captured; separate root diagnostic font/looper exceptions are not system crashes')
(trial/'result.json').write_text(json.dumps(report,indent=2)+'\n')
status=p/'CURRENT-STATUS.md';s=status.read_text(encoding='utf-8')
prefix='''## CURRENT: v21 same boot; setup app compatibility candidate building - 2026-11-07 15:49

User confirms touch responds and Recents "No recent items" draws correctly. Welcome remains corrupt/stale with top stripes; NOT a working-ROM pass. Current tablet root Android, trial hardware-tests/20261107-151636-core, server354, v21 system + v27 BOOT. No new reboot since151636. Prior runner85154 completed stability; no runner active. v21 manifest/result now reflect failed display validation.

ONLY build24211 runs scripts/build_setup_candidate.sh in T110Build, log /root/t110-build/logs/setup-canvas-20261107T134653Z.log. Patch0057 adds a default-true SetupWizard hardwareAcceleration resource; T110 device overlay selects false. This is an app-specific compatibility candidate, not yet proven. Once built, verify APK platform signature matches c8a2e9bccf597c2fb6dc66bee293fc13f2fc47ec77bc6b2b0d52c11f51192ab8, actual manifest resource and compiled overlay false, then install app update on this same boot (adb install -r -t), launch Welcome, capture selected fb page and confirm CPU window path. NO full ROM build/flash yet. Only bake into system if actual Welcome corrected. Standing user auto-flash authorization applies after corrected ROM is ready; no approval/readiness stops.

New same-boot evidence: evidence/offline-v32/readback has clean software and HWUI GPU frames at600x1024 and1024x600. Raw ImageReader CPU readback avoids SF. Buffer display comparison0xb00 vs0xb03 handed same HWUI frame directly to SF: quadrants correct in both; GPU-only case small black triangle at edge, CPU-readable perfect. Early CanvasProbe GPU captures INVALID because main thread slept before BLAST posted; later main looper run did post but attempted quit caused diagnostic exception. Do not confuse its font/looper diagnostic crashes with actual SetupWizard EGL_BAD_ACCESS. Run_canvas_comparison is obsolete pending cleanup. debug.hwui.use_partial_updates tested false for SetupWizard but no visible fix; restored true (original unset/default true). No persistent ROM property change. Currently setupAPK baseline pulled to evidence/offline-v32/setup-original.apk.

WSL persistent shell40319 keeps distro alive. No other diagnostic processes active; buffer display59223 and readback35800 completed0. No agents. Android source current build inputs must not be edited during24211. Source route remains T110Build:/root/t110-build/lineage20; kernel unchanged Ubuntu out-storage-acl.

'''
status.write_text(prefix+s,encoding='utf-8')
print('V21_FINDINGS_RECORDED')
