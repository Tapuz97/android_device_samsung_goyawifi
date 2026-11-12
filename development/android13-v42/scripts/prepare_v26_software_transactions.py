from pathlib import Path
import subprocess,difflib
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
t=Path('/root/t110-build/lineage20/packages/apps/Trebuchet')
name='quickstep/src/com/android/quickstep/util/SurfaceTransactionApplier.java'
old=(t/name).read_text();assert 'T110SoftwareSurface' not in old
new=old.replace('    private int mLastSequenceNumber = 0;','    private int mLastSequenceNumber = 0;\n    private boolean mSoftwarePathLogged;')
anchor='''        setCanRelease(false);
        mTargetViewRootImpl.registerRtFrameCallback(frame -> {'''
assert new.count(anchor)==1
new=new.replace(anchor,'''        setCanRelease(false);
        if ("t110_bringup".equals(Build.DEVICE) && !view.isHardwareAccelerated()) {
            // Software windows have no RenderThread to deliver this callback.
            // Submit their transform transaction directly, and keep the same
            // ordered release bookkeeping as the hardware callback below.
            if (mBarrierSurfaceControl != null && mBarrierSurfaceControl.isValid()) {
                t.apply();
            }
            Message.obtain(mApplyHandler, MSG_UPDATE_SEQUENCE_NUMBER, toApplySeqNo, 0)
                    .sendToTarget();
            if (!mSoftwarePathLogged) {
                android.util.Log.d("T110SoftwareSurface",
                        "Applying launcher surface transaction without RenderThread");
                mSoftwarePathLogged = true;
            }
            view.invalidate();
            return;
        }
        mTargetViewRootImpl.registerRtFrameCallback(frame -> {''')
patch=p/'patches/0068-trebuchet-t110-software-surface-transactions.patch'
assert not patch.exists()
patch.write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+name,tofile='b/'+name)),encoding='utf-8')
subprocess.run(['git','apply','--check',str(patch)],cwd=t,check=True)
subprocess.run(['git','apply',str(patch)],cwd=t,check=True)
build=p/'scripts/build_system_image.sh';s=build.read_text()
anchor="'packages/apps/Trebuchet:0067-trebuchet-t110-software-frame-completion.patch'"
assert s.count(anchor)==1
build.write_text(s.replace(anchor,anchor+" 'packages/apps/Trebuchet:0068-trebuchet-t110-software-surface-transactions.patch'"),encoding='utf-8')
print('SOFTWARE_SURFACE_TRANSACTIONS_PREPARED')
