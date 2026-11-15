"""Use the native dim-layer fade instead of reprojecting the rotated screenshot."""
from pathlib import Path
helper=Path(__file__).with_name('apply_modern_ui.py').read_text()
exec(helper[:helper.index("FW='frameworks/base/'")])
path='frameworks/base/services/core/java/com/android/server/display/ColorFade.java'
edit(path,'''        // Prepare the surface for drawing.
        if (!(createSurface()''','''        // MODE_FADE is a compositor dim layer, not a screenshot/GL animation.
        // In particular, avoid reprojecting the T110's 270-degree board capture.
        if (mMode == MODE_FADE) {
            mPrepared = true;
            if (!createSurface()) {
                dismiss();
                return false;
            }
            return true;
        }

        // Prepare the surface for drawing.
        if (!(createSurface()''')
edit(path,'''                mSurface = new Surface();
                mSurface.copyFrom(mSurfaceControl);''','''                if (mMode != MODE_FADE) {
                    mSurface = new Surface();
                    mSurface.copyFrom(mSurfaceControl);
                }''')
edit(path,'''                mSurfaceControl.destroy();
                mSurface.release();''','''                mSurfaceControl.destroy();
                if (mSurface != null) {
                    mSurface.release();
                    mSurface = null;
                }''')
path='device/samsung/goyawifi/overlay/frameworks/base/core/res/res/values/config.xml'
edit(path,'</resources>','''    <!-- A pure dim layer keeps lock transitions off the rotated capture/GL path. -->
    <bool name="config_animateScreenLights">true</bool>
</resources>''')
path='frameworks/base/services/core/java/com/android/server/display/DisplayPowerController.java'
edit(path,'''        mColorFadeOffAnimator.setDuration(COLOR_FADE_OFF_ANIMATION_DURATION_MILLIS);''','''        mColorFadeOffAnimator.setDuration(mColorFadeFadesConfig
                ? mContext.getResources().getInteger(android.R.integer.config_shortAnimTime)
                : COLOR_FADE_OFF_ANIMATION_DURATION_MILLIS);''')
print('Native dim-layer fade selected for T110; no screenshot, EGL surface or shader in MODE_FADE.')
