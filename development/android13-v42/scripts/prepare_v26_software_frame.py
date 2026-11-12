from pathlib import Path
import difflib, subprocess

p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
t=Path('/root/t110-build/lineage20/packages/apps/Trebuchet')
name='quickstep/src/com/android/quickstep/ViewUtils.java'
old=(t/name).read_text()
needle='        return new FrameHandler(view, onFinishRunnable, canceled).schedule();'
assert old.count(needle)==1 and 'T110SoftwareFrameHandler' not in old
new=old.replace(needle,'''        if ("t110_bringup".equals(android.os.Build.DEVICE)
                && !view.isHardwareAccelerated()) {
            return new T110SoftwareFrameHandler(view, onFinishRunnable, canceled).schedule();
        }
'''+needle)
helper='quickstep/src/com/android/quickstep/T110SoftwareFrameHandler.java'
assert not (t/helper).exists()
code='''package com.android.quickstep;

import android.os.Handler;
import android.util.Log;
import android.view.SurfaceControl;
import android.view.View;
import android.view.ViewRootImpl;
import android.view.ViewTreeObserver;
import java.util.function.BooleanSupplier;

/** Completes transitions after software Canvas has posted two actual window draws. */
final class T110SoftwareFrameHandler implements ViewTreeObserver.OnDrawListener,
        ViewRootImpl.SurfaceChangedCallback {
    private final ViewRootImpl mRoot;
    private final Runnable mCallback;
    private final BooleanSupplier mCancelled;
    private final Handler mHandler = new Handler();
    private ViewTreeObserver mObserver;
    private boolean mSurfaceRegistered;
    private boolean mPosted;
    private boolean mFinished;
    private int mFramesRemaining = 2;

    T110SoftwareFrameHandler(View view, Runnable callback, BooleanSupplier cancelled) {
        mRoot = view.getViewRootImpl();
        mCallback = callback;
        mCancelled = cancelled;
    }

    boolean schedule() {
        if (mFinished || mRoot == null || mRoot.getView() == null) return false;
        View rootView = mRoot.getView();
        ViewTreeObserver observer = rootView.getViewTreeObserver();
        if (!observer.isAlive()) return false;
        if (!mSurfaceRegistered) {
            mRoot.addSurfaceChangedCallback(this);
            mSurfaceRegistered = true;
            Log.d("T110SoftwareFrame", "Using software draw completion for launcher transition");
        }
        mObserver = observer;
        mObserver.addOnDrawListener(this);
        rootView.invalidate();
        return true;
    }

    @Override
    public void onDraw() {
        if (mPosted || mFinished) return;
        mPosted = true;
        // A normal Handler post runs after this traversal returns, including the
        // software Canvas unlock/post. Never remove listeners during onDraw.
        mHandler.post(() -> {
            removeDrawListener();
            mPosted = false;
            if (mFinished) return;
            if (mCancelled.getAsBoolean()) {
                finish(false);
            } else if (--mFramesRemaining == 0 || !schedule()) {
                finish(true);
            }
        });
    }

    private void removeDrawListener() {
        if (mObserver != null) {
            if (mObserver.isAlive()) mObserver.removeOnDrawListener(this);
            mObserver = null;
        }
    }

    private void finish(boolean invokeCallback) {
        if (mFinished) return;
        mFinished = true;
        removeDrawListener();
        if (mSurfaceRegistered) {
            mRoot.removeSurfaceChangedCallback(this);
            mSurfaceRegistered = false;
        }
        if (invokeCallback && !mCancelled.getAsBoolean() && mCallback != null) {
            mCallback.run();
        }
    }

    @Override public void surfaceCreated(SurfaceControl.Transaction transaction) { }
    @Override public void surfaceReplaced(SurfaceControl.Transaction transaction) { }
    @Override public void surfaceDestroyed() { finish(true); }
}
'''
patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
patch+=''.join(difflib.unified_diff([],code.splitlines(True),fromfile='/dev/null',tofile='b/'+helper))
dest=p/'patches/0067-trebuchet-t110-software-frame-completion.patch'
assert not dest.exists();dest.write_text(patch,encoding='utf-8')
subprocess.run(['git','apply','--check',str(dest)],cwd=t,check=True)
subprocess.run(['git','apply',str(dest)],cwd=t,check=True)
build=p/'scripts/build_system_image.sh';s=build.read_text()
anchor="'frameworks/base:0066-systemui-respect-strictmode-default-optout.patch'"
assert s.count(anchor)==1
build.write_text(s.replace(anchor,anchor+" 'packages/apps/Trebuchet:0067-trebuchet-t110-software-frame-completion.patch'"),encoding='utf-8')
e=p/'evidence/offline-v36';(e/'launcher-candidate').mkdir(parents=True,exist_ok=True)
candidate=(p/'scripts/build_launcher_candidate.sh').read_text().replace('launcher-canvas-','launcher-frame-').replace('offline-v34','offline-v36')
(p/'scripts/build_launcher_frame_candidate.sh').write_text(candidate,encoding='utf-8')
print('SOFTWARE_FRAME_COMPLETION_PATCH_APPLIED')
