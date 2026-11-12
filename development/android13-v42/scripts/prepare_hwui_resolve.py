"""Integrate the scoped, pixel-verified Vivante window resolve into native HWUI."""
from pathlib import Path
import difflib,hashlib,json,subprocess,sys
p=Path(__file__).resolve().parents[1];tree=Path(sys.argv[1]);repo=tree/'frameworks/base';e=p/'evidence/hardware-v35'
fixture=json.loads((e/'hwui-one-pixel-panel-suite.json').read_text())
assert fixture['render_result']['completed'] and fixture['render_result']['hwui_suite']['all_pixels_match']
assert len(fixture['render_result']['hwui_suite']['cases'])==6
assert fixture['settings_restored'] and all(fixture['settings_restored'].values())
edits={
 'libs/hwui/renderthread/EglManager.cpp':[(
 '    EGLint rects[4];\n    frame.map(screenDirty, rects);\n',
 '''    // The stock T110 Vivante driver leaves window geometry in an unresolved
    // render target across swap, even after glFinish. A one-pixel read forces
    // its legacy window resolve without reading the full frame. Full-panel
    // geometry, clipping, texture and surface-recreation fixtures validate it.
    static const bool legacyT110 = property_get_bool("ro.t110.legacy_gpu", false);
    if (legacyT110) {
        GLubyte pixel[4];
        glReadPixels(0, 0, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, pixel);
    }

    EGLint rects[4];
    frame.map(screenDirty, rects);
''')],
 'core/java/android/view/ViewRootImpl.java':[(
 '''        // The T110's stock EGL driver corrupts normal HWUI window frames and can
        // abort in swapBuffers. Use the existing software View/Canvas path for
        // this engineering device, as already validated by its setup activity.
        // SurfaceView, direct GLES clients and SurfaceFlinger remain separate.
        // Keep this opt-in under the existing exported device compatibility flag.
        if (SystemProperties.getBoolean("ro.t110.legacy_gpu", false)) {''',
 '''        // Native HWUI now resolves the T110's legacy Vivante window before
        // presenting it. Keep the validated software path available for diagnosis
        // while using normal accelerated rendering by default.
        if (SystemProperties.getBoolean("ro.t110.legacy_gpu", false)
                && !SystemProperties.getBoolean("debug.hwui.t110_window_gpu", true)) {''')]
}
patch=p/'patches/0098-hwui-t110-resolve-window-before-presentation.patch'
if not patch.exists():
 chunks=[]
 for name,replacements in edits.items():
  before=(repo/name).read_text();after=before
  for old,new in replacements:assert after.count(old)==1,name;after=after.replace(old,new,1)
  chunks.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),'a/'+name,'b/'+name))
 patch.write_text(''.join(chunks),encoding='utf-8')
command=['git','-C',str(repo),'apply']
if subprocess.run(command+['--reverse','--check',str(patch)],capture_output=True).returncode:
 subprocess.run(command+['--check',str(patch)],check=True);subprocess.run(command+[str(patch)],check=True)
record=dict(status='SOURCE_APPLIED_BUILD_PENDING',production_app_validation=False,patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),
 fixture='hwui-one-pixel-panel-suite.json',files={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in edits})
(e/'hwui-source.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print('HWUI_RESOLVE_SOURCE_READY')
