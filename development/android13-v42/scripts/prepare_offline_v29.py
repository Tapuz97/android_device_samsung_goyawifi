"""Correct the captured T110 panel orientation and framebuffer power contract."""
from pathlib import Path
import difflib
import json
import subprocess

p = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
tree = Path('/root/t110-build/lineage20')
evidence = p/'evidence/offline-v29'
evidence.mkdir(exist_ok=True)

def replace(path, old, new):
    text = path.read_text()
    assert text.count(old) == 1, (str(path), old[:90])
    (evidence/(path.name+'.before')).write_text(text)
    path.write_text(text.replace(old, new))

product = p/'work/device/samsung/t110_bringup/t110_system.mk'
replace(product, 'TARGET_SCREEN_WIDTH := 1024\nTARGET_SCREEN_HEIGHT := 600',
        'TARGET_SCREEN_WIDTH := 600\nTARGET_SCREEN_HEIGHT := 1024')
replace(product, 'PRODUCT_SYSTEM_PROPERTIES += ro.sf.lcd_density=160',
        '''PRODUCT_SYSTEM_PROPERTIES += ro.sf.lcd_density=160
# Stock T110 build.prop specifies hwrotation=270. Let SurfaceFlinger expose
# the natural 600x1024 portrait display and undo panel rotation for input.
PRODUCT_SYSTEM_PROPERTIES += ro.surface_flinger.primary_display_orientation=ORIENTATION_270''')
native = tree/'frameworks/native'
renderer = native/'libs/renderengine/gl/GLESRenderEngine.cpp'
replace(renderer, '''        // FBO targets use a top-row memory convention. An EGL window uses the
        // GL bottom-left convention; mirror projection and scissor together.
        mState.projectionMatrix = mat4(vec4(1, -1, 1, 1)) * mState.projectionMatrix;
''', '''        // The EGL window's final clip-space Y inversion is applied after
        // display orientation below. Scissor uses framebuffer coordinates.
''')
replace(renderer, '''    const mat4 projectionMatrix =
            ui::Transform(display.orientation).asMatrix4() * mState.projectionMatrix;
''', '''    mat4 projectionMatrix =
            ui::Transform(display.orientation).asMatrix4() * mState.projectionMatrix;
    if (legacyWindow) {
        // Flip the final output convention, after rotation. Rotation and this
        // reflection do not commute at 90/270 degrees.
        projectionMatrix = mat4(vec4(1, -1, 1, 1)) * projectionMatrix;
    }
''')

hardware = tree/'hardware/interfaces'
adapter = hardware/'graphics/composer/2.1/utils/hwc2onfbadapter/HWC2OnFbAdapter.cpp'
replace(adapter, 'int32_t setPowerModeHook(hwc2_device_t* device, hwc2_display_t display, int32_t /*mode*/)',
        'int32_t setPowerModeHook(hwc2_device_t* device, hwc2_display_t display, int32_t mode)')
replace(adapter, '''    // pretend that it works
    return HWC2_ERROR_NONE;
}

int32_t setVsyncEnabledHook''', '''    return adapter.setPowerMode(mode);
}

int32_t setVsyncEnabledHook''')
replace(adapter, 'bool HWC2OnFbAdapter::postBuffer() {', '''int32_t HWC2OnFbAdapter::setPowerMode(int32_t mode) {
    // Preserve the old adapter contract for framebuffer HALs without this hook.
    if (!mFbDevice->enableScreen) return HWC2_ERROR_NONE;
    int enable;
    switch (mode) {
        case HWC2_POWER_MODE_OFF: enable = 0; break;
        case HWC2_POWER_MODE_ON: enable = 1; break;
        case HWC2_POWER_MODE_DOZE:
        case HWC2_POWER_MODE_DOZE_SUSPEND: return HWC2_ERROR_UNSUPPORTED;
        default: return HWC2_ERROR_BAD_PARAMETER;
    }
    return mFbDevice->enableScreen(mFbDevice, enable) == 0
            ? HWC2_ERROR_NONE : HWC2_ERROR_UNSUPPORTED;
}

bool HWC2OnFbAdapter::postBuffer() {''')
header = hardware/'graphics/composer/2.1/utils/hwc2onfbadapter/include/hwc2onfbadapter/HWC2OnFbAdapter.h'
replace(header, '    bool postBuffer();', '    bool postBuffer();\n    int32_t setPowerMode(int32_t mode);')
framebuffer = hardware/'graphics/composer/2.1/default/T110Framebuffer.cpp'
replace(framebuffer, '    int lastError = 0;', '    int lastError = 0;\n    bool blanked = false;')
replace(framebuffer, 'int closeDevice(hw_device_t* device) {', '''int enableScreen(framebuffer_device_t* fb, int enable) {
    auto* d = reinterpret_cast<Device*>(fb);
    std::lock_guard<std::mutex> guard(d->mutex);
    if (enable != 0 && enable != 1) return -EINVAL;
    // FBIOBLANK takes the blank level directly, not a pointer. This is the
    // checked PXA fb driver's runtime-PM blank/unblank entrypoint.
    const int level = enable ? FB_BLANK_UNBLANK : FB_BLANK_POWERDOWN;
    if (ioctl(d->fd, FBIOBLANK, level) < 0) {
        const int error = -errno;
        ALOGE("T110 framebuffer power transition failed: enable=%d error=%d", enable, error);
        return error;
    }
    d->blanked = !enable;
    ALOGI("T110 framebuffer power: %s", enable ? "on" : "off");
    return 0;
}
int closeDevice(hw_device_t* device) {''')
replace(framebuffer, '''"T110 direct fb0 scanout: frames=%llu yoffset=%u error=%d\\n",
                          static_cast<unsigned long long>(d->frames), d->mode.yoffset, d->lastError);''',
        '''"T110 direct fb0 scanout: frames=%llu yoffset=%u error=%d blanked=%d\\n",
                          static_cast<unsigned long long>(d->frames), d->mode.yoffset, d->lastError,
                          static_cast<int>(d->blanked));''')
replace(framebuffer, '    d->fb.post = post;', '    d->fb.post = post;\n    d->fb.enableScreen = enableScreen;')
(p/'work/T110Framebuffer.cpp').write_bytes(framebuffer.read_bytes())

def combined(repo, old_patch, extra_paths, output):
    names = [line[6:] for line in (p/'patches'/old_patch).read_text().splitlines()
             if line.startswith('+++ b/')]
    names += extra_paths
    result = []
    for name in dict.fromkeys(names):
        before = subprocess.run(['git','show','HEAD:'+name], cwd=repo, capture_output=True, text=True)
        old = before.stdout if before.returncode == 0 else ''
        after = (repo/name).read_text()
        result.append('diff --git a/'+name+' b/'+name+'\n')
        if before.returncode: result.append('new file mode 100644\n')
        result.extend(difflib.unified_diff(old.splitlines(True), after.splitlines(True),
                      'a/'+name if before.returncode == 0 else '/dev/null', 'b/'+name))
    patch = p/'patches'/output
    patch.write_text(''.join(result))
    subprocess.run(['git','apply','--reverse','--check',str(patch)], cwd=repo, check=True)

combined(native, '0038-renderengine-t110-egl-window-bridge.patch', [],
         '0053-renderengine-t110-oriented-window-bridge.patch')
combined(hardware, '0036-composer-t110-synchronized-scanout.patch',
         ['graphics/composer/2.1/utils/hwc2onfbadapter/HWC2OnFbAdapter.cpp',
          'graphics/composer/2.1/utils/hwc2onfbadapter/include/hwc2onfbadapter/HWC2OnFbAdapter.h'],
         '0054-composer-t110-scanout-and-display-power.patch')
script = p/'scripts/build_system_image.sh'
replace(script, '0038-renderengine-t110-egl-window-bridge.patch',
        '0053-renderengine-t110-oriented-window-bridge.patch')
replace(script, '0036-composer-t110-synchronized-scanout.patch',
        '0054-composer-t110-scanout-and-display-power.patch')
(evidence/'preparation.json').write_text(json.dumps(dict(
    status='SOURCE_PREPARED', primary_display_orientation='ORIENTATION_270',
    natural_display=[600,1024], stock_rotation_source='stock/T110XXUANI7/system/build.prop',
    touch_extra_rotation=False, note='SurfaceFlinger removes physical rotation from InputFlinger coordinates.',
    renderer_flip_after_rotation=True, framebuffer_power_hook=True,
    superseded_patches=['0038','0036'], tablet_writes=False), indent=2)+'\n')
print('ORIENTATION_AND_DISPLAY_POWER_PREPARED')
