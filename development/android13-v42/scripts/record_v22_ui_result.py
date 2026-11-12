"""Record the observed v22 UI result without overstating the boot flag."""
from pathlib import Path
import datetime
import json

p=Path(__file__).resolve().parents[1]
trial='hardware-tests/20261107-161729-core'
file=p/'artifacts/lineage20-rom-v22/rom-pair.json'
pair=json.loads(file.read_text())
pair.update(status='BOOTED_SETUP_COMPLETED_LAUNCHER_AND_GRAPHICS_FAILED',
    hardware_tested=True,hardware_validated=False,full_boot_passed=False,
    trial=trial,user_setup_completed=True,touch_confirmed_by_user=True,
    setup_rendering_confirmed=True,
    remaining_failures=['Launcher loader crashes: AppWidgetManager is null; appwidget service absent',
                        'Launcher RenderThread aborts with EGL_BAD_ACCESS',
                        'Settings and home graphics remain corrupt'],
    limits=['Ordinary app graphics remain unusable',
            'Wi-Fi radio/audio and other hardware remain unported'])
file.write_text(json.dumps(pair,indent=2)+'\n',encoding='utf-8')
report=dict(observed_at=datetime.datetime.now().astimezone().isoformat(),
    trial=trial,system_server_pid=365,boot_completed=True,user_unlocked=True,
    device_provisioned=True,user_setup_complete=True,touch='User completed setup and reports responsive touch',
    launcher_failure='AppWidgetManager null: pm has-feature android.software.app_widgets false; service appwidget absent',
    graphics_failure='RenderThread EGL_BAD_ACCESS; active framebuffer shows corrupt Settings/home',
    hardware_navigation='Kernel exposes HOME, MENU, BACK; settings integration deferred at user request',
    next='Combined v23 widget declaration plus device-only ViewRoot software Canvas fallback')
(p/'evidence/offline-v33/v22-runtime-result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
status=p/'CURRENT-STATUS.md'
status.write_text('''## Current: v22 booted, setup and touch confirmed; launcher/graphics still fail

Trial hardware-tests/20261107-161729-core completed its 180-second core stability observation; runner91674 is finished. Tablet remains on Android v22 system + v27 BOOT, system_server365. User physically completed setup and confirms responsive touch. This is NOT a usable-ROM pass: launcher repeatedly crashes because AppWidgetService is absent, and EGL_BAD_ACCESS plus corrupt ordinary app windows remain. v22 rom-pair.json now records the actual result.

Preparing v23: canonical app_widgets feature to start the missing service; existing basic touchscreen feature; patch0058 makes T110 ViewRoot windows use the software Canvas path proven for SetupWizard. Direct GLES/SurfaceView and SurfaceFlinger are unchanged. Hardware navigation settings are deferred per user request. No new boot yet. Current same-boot diagnostic set debug.hwui.use_partial_updates=false; this is temporary and must be reset before the next full boot. No other app updates were installed after v22. Build SSD was reconnected after read retries; T110Build is accessible again. Use the current live tool/process state before starting a build.

'''+status.read_text(encoding='utf-8'),encoding='utf-8')
print('V22_ACTUAL_RESULT_RECORDED')
