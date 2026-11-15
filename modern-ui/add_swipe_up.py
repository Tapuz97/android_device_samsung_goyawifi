"""Native launcher gesture; hide the old button while keeping its reveal anchor."""
from pathlib import Path
import xml.etree.ElementTree as ET
helper=Path(__file__).with_name('apply_modern_ui.py').read_text()
exec(helper[:helper.index("FW='frameworks/base/'")])
APP='packages/apps/Trebuchet/'
save(APP+'src/com/android/launcher3/util/HomeSwipeDetector.java',
     Path(__file__).with_name('swipe-up').joinpath('HomeSwipeDetector.java').read_text())

path=APP+'src/com/android/launcher3/DragLayer.java'
edit(path,'import android.view.ViewGroup;','import android.view.ViewGroup;\nimport android.view.ViewConfiguration;')
edit(path,'import com.android.launcher3.util.Thunk;',
     'import com.android.launcher3.util.Thunk;\nimport com.android.launcher3.util.HomeSwipeDetector;')
edit(path,'    private boolean mBlockTouches = false;', '''    private boolean mBlockTouches = false;
    private final HomeSwipeDetector mHomeSwipe;
    private boolean mHomeSwipeIntercepted;''')
edit(path,'        mIsRtl = Utilities.isRtl(res);','''        mIsRtl = Utilities.isRtl(res);
        int slop = ViewConfiguration.get(context).getScaledTouchSlop();
        mHomeSwipe = new HomeSwipeDetector(Math.max(48 * res.getDisplayMetrics().density,
                4 * slop), slop, ViewConfiguration.getLongPressTimeout());''')
edit(path,'    @Override\n    public boolean onInterceptTouchEvent(MotionEvent ev) {','''    private boolean canOpenAppsFromHome() {
        if (mLauncher == null || mDragController == null || mBlockTouches
                || mCurrentResizeFrame != null || mDragController.isDragging()
                || (mOverlayView != null && mOverlayView.getParent() != null)) return false;
        Workspace workspace = mLauncher.getWorkspace();
        return workspace != null && workspace.getState() == Workspace.State.NORMAL
                && !workspace.isSwitchingState() && !mLauncher.isAppsViewVisible()
                && !workspace.isOnOrMovingToCustomContent() && workspace.getOpenFolder() == null;
    }

    private boolean canStartHomeSwipe(MotionEvent event) {
        if (!canOpenAppsFromHome()) return false;
        Workspace workspace = mLauncher.getWorkspace();
        Rect bounds = new Rect();
        getDescendantRectRelativeToSelf(workspace, bounds);
        boolean inside = bounds.contains((int) event.getX(), (int) event.getY());
        getDescendantRectRelativeToSelf(mLauncher.getHotseat(), bounds);
        inside |= bounds.contains((int) event.getX(), (int) event.getY());
        if (!inside) return false;
        View page = workspace.getChildAt(workspace.getCurrentPage());
        if (page instanceof CellLayout) {
            ViewGroup children = ((CellLayout) page).getShortcutsAndWidgets();
            for (int i = 0; i < children.getChildCount(); i++) {
                View child = children.getChildAt(i);
                if (child.getTag() instanceof LauncherAppWidgetInfo) {
                    getDescendantRectRelativeToSelf(child, bounds);
                    if (bounds.contains((int) event.getX(), (int) event.getY())) return false;
                }
            }
        }
        return true;
    }

    @Override
    public void requestDisallowInterceptTouchEvent(boolean disallow) {
        if (disallow && !mHomeSwipeIntercepted) mHomeSwipe.cancel();
        super.requestDisallowInterceptTouchEvent(disallow);
    }

    @Override
    public boolean onInterceptTouchEvent(MotionEvent ev) {''')
edit(path,'''        int action = ev.getAction();

        if (action == MotionEvent.ACTION_DOWN) {
            if (handleTouchDown(ev, true)) {
                return true;''','''        int action = ev.getAction();
        if (ev.getActionMasked() == MotionEvent.ACTION_DOWN) {
            mHomeSwipeIntercepted = false;
            mHomeSwipe.begin(ev.getX(), ev.getY(), ev.getEventTime(), canStartHomeSwipe(ev));
        } else if (ev.getActionMasked() == MotionEvent.ACTION_POINTER_DOWN
                || action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
            mHomeSwipe.cancel();
        }

        if (action == MotionEvent.ACTION_DOWN) {
            if (handleTouchDown(ev, true)) {
                mHomeSwipe.cancel();
                return true;''')
edit(path,'''        clearAllResizeFrames();
        return mDragController.onInterceptTouchEvent(ev);''','''        clearAllResizeFrames();
        if (mDragController.onInterceptTouchEvent(ev)) {
            mHomeSwipe.cancel();
            return true;
        }
        if (!canOpenAppsFromHome()) mHomeSwipe.cancel();
        if (ev.getActionMasked() == MotionEvent.ACTION_MOVE
                && mHomeSwipe.move(ev.getX(), ev.getY(), ev.getEventTime(), ev.getPointerCount())) {
            mHomeSwipeIntercepted = true;
            return true;
        }
        return false;''')
old_header='    public boolean onTouchEvent(MotionEvent ev) {\n        if (mHomeSwipeIntercepted) {'
if old_header in read(path):
    edit(path,old_header,'''    public boolean onTouchEvent(MotionEvent ev) {
        // Empty dock space may have no child touch target. Observe that stream
        // here as well as in interception, without stealing a child's DOWN.
        if (!mHomeSwipeIntercepted && ev.getActionMasked() == MotionEvent.ACTION_MOVE) {
            if (!canOpenAppsFromHome()) mHomeSwipe.cancel();
            mHomeSwipeIntercepted = mHomeSwipe.move(ev.getX(), ev.getY(),
                    ev.getEventTime(), ev.getPointerCount());
        }
        if (mHomeSwipeIntercepted) {''')
edit(path,'    public boolean onTouchEvent(MotionEvent ev) {\n        boolean handled = false;', '''    public boolean onTouchEvent(MotionEvent ev) {
        // Empty dock space may have no child touch target. Observe that stream
        // here as well as in interception, without stealing a child's DOWN.
        if (!mHomeSwipeIntercepted && ev.getActionMasked() == MotionEvent.ACTION_MOVE) {
            if (!canOpenAppsFromHome()) mHomeSwipe.cancel();
            mHomeSwipeIntercepted = mHomeSwipe.move(ev.getX(), ev.getY(),
                    ev.getEventTime(), ev.getPointerCount());
        }
        if (mHomeSwipeIntercepted) {
            int maskedAction = ev.getActionMasked();
            if (!canOpenAppsFromHome()) mHomeSwipe.cancel();
            if (maskedAction == MotionEvent.ACTION_MOVE) {
                mHomeSwipe.move(ev.getX(), ev.getY(), ev.getEventTime(), ev.getPointerCount());
            } else if (maskedAction == MotionEvent.ACTION_POINTER_DOWN) {
                mHomeSwipe.cancel();
            } else if (maskedAction == MotionEvent.ACTION_UP
                    || maskedAction == MotionEvent.ACTION_CANCEL) {
                boolean open = maskedAction == MotionEvent.ACTION_UP
                        && mHomeSwipe.end(ev.getX(), ev.getY(), ev.getPointerCount());
                mHomeSwipe.cancel();
                mHomeSwipeIntercepted = false;
                if (mTouchCompleteListener != null) mTouchCompleteListener.onTouchComplete();
                mTouchCompleteListener = null;
                if (open && canOpenAppsFromHome()) {
                    post(new Runnable() {
                        @Override
                        public void run() {
                            if (canOpenAppsFromHome()) {
                                mLauncher.showAppsView(true, true, true, false);
                            }
                        }
                    });
                }
            }
            return true;
        }
        boolean handled = false;''')
edit(path,'        return mDragController.onTouchEvent(ev);','''        boolean dragging = mDragController.onTouchEvent(ev);
        if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) mHomeSwipe.cancel();
        return dragging || mHomeSwipe.isTracking();''')

# Preserve saved dock ranks and the animation's laid-out anchor. The anchor
# is not visible, clickable, focusable or exposed as an accessibility button.
path=APP+'src/com/android/launcher3/Hotseat.java'
edit(path,'        mContent.addViewToCellLayout(allAppsButton, -1, allAppsButton.getId(), lp, true);',
'''        mContent.addViewToCellLayout(allAppsButton, -1, allAppsButton.getId(), lp, true);
        allAppsButton.setVisibility(INVISIBLE);
        allAppsButton.setClickable(false);
        allAppsButton.setLongClickable(false);
        allAppsButton.setFocusable(false);
        allAppsButton.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);''')
path=APP+'src/com/android/launcher3/LauncherStateTransitionAnimation.java'
save(path,read(path).replace('allAppsButtonView.setVisibility(View.VISIBLE);',
                            'allAppsButtonView.setVisibility(View.INVISIBLE);'))
save(APP+'res/values/t110_swipe_up.xml',xml('''<resources>
    <item name="t110_action_open_all_apps" type="id" />
</resources>'''))
path=APP+'src/com/android/launcher3/Workspace.java'
edit(path,'import android.view.accessibility.AccessibilityManager;',
     'import android.view.accessibility.AccessibilityManager;\nimport android.view.accessibility.AccessibilityNodeInfo;')
edit(path,'    public void updateAccessibilityFlags() {','''    @Override
    public void onInitializeAccessibilityNodeInfo(AccessibilityNodeInfo info) {
        super.onInitializeAccessibilityNodeInfo(info);
        if (mLauncher != null && mState == State.NORMAL && !isSwitchingState()
                && getOpenFolder() == null && !isOnOrMovingToCustomContent()) {
            info.addAction(new AccessibilityNodeInfo.AccessibilityAction(
                    R.id.t110_action_open_all_apps, getContext().getString(R.string.all_apps_button_label)));
        }
    }

    @Override
    public boolean performAccessibilityAction(int action, Bundle arguments) {
        if (action == R.id.t110_action_open_all_apps && mLauncher != null
                && mState == State.NORMAL && !isSwitchingState() && !mDragController.isDragging()
                && getOpenFolder() == null && !isOnOrMovingToCustomContent()) {
            mLauncher.showAppsView(true, true, true, false);
            return true;
        }
        return super.performAccessibilityAction(action, arguments);
    }

    public void updateAccessibilityFlags() {''')
edit(path,
     'setImportantForAccessibility((mState == State.NORMAL || mState == State.OVERVIEW)\n                    ? IMPORTANT_FOR_ACCESSIBILITY_AUTO',
     'setImportantForAccessibility((mState == State.NORMAL || mState == State.OVERVIEW)\n                    ? (mState == State.NORMAL ? IMPORTANT_FOR_ACCESSIBILITY_YES\n                            : IMPORTANT_FOR_ACCESSIBILITY_AUTO)')
for name in files:
    if name.endswith('.xml'):ET.parse(SRC/name)
print('Native swipe-up added; button stays hidden in creation and both animations; accessibility action retained.')
