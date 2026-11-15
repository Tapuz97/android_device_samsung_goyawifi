"""Native drawer dismissal, no alphabet footer, and a continuous drawer surface."""
from pathlib import Path
import xml.etree.ElementTree as ET
helper=Path(__file__).with_name('apply_modern_ui.py').read_text()
exec(helper[:helper.index("FW='frameworks/base/'")])
APP='packages/apps/Trebuchet/'
path=APP+'src/com/android/launcher3/allapps/AllAppsContainerView.java'
edit(path,'import com.android.launcher3.util.Thunk;',
     'import com.android.launcher3.util.Thunk;\nimport com.android.launcher3.util.HomeSwipeDetector;')
edit(path,'    private boolean mReloadDrawer = false;','''    private boolean mReloadDrawer = false;
    private final HomeSwipeDetector mDismissSwipe;
    private boolean mDismissSwipeCaptured;''')
edit(path,'        mLauncher = (Launcher) context;','''        mLauncher = (Launcher) context;
        int slop = ViewConfiguration.get(context).getScaledTouchSlop();
        mDismissSwipe = new HomeSwipeDetector(Math.max(48 * res.getDisplayMetrics().density,
                4 * slop), slop, ViewConfiguration.getLongPressTimeout());''')
edit(path,'        mGridTheme = useDarkColor ? GRID_THEME_DARK : GRID_THEME_LIGHT;','''        mGridTheme = useDarkColor ? GRID_THEME_DARK : GRID_THEME_LIGHT;
        // One continuous drawer surface instead of separate floating panels.
        setBackgroundColor(getResources().getColor(useDarkColor
                ? R.color.quantum_panel_bg_color_dark : R.color.quantum_panel_bg_color));''')
edit(path,'    @Override\n    public boolean onInterceptTouchEvent(MotionEvent ev) {','''    private boolean canDismissDrawer() {
        return mAppsRecyclerView != null && mLauncher.isAppsViewVisible()
                && !mLauncher.getWorkspace().isSwitchingState()
                && !mLauncher.getDragController().isDragging() && !mApps.hasFilter()
                && !mAppsRecyclerView.canScrollVertically(-1);
    }

    private boolean canStartDismissSwipe(MotionEvent event) {
        if (!canDismissDrawer()) return false;
        Rect bounds = new Rect();
        mAppsRecyclerView.getGlobalVisibleRect(bounds);
        return bounds.contains((int) event.getRawX(), (int) event.getRawY());
    }

    @Override
    public boolean dispatchTouchEvent(MotionEvent event) {
        int action = event.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) {
            mDismissSwipeCaptured = false;
            // Negate Y to reuse the tested upward recognizer for downward motion.
            mDismissSwipe.begin(event.getX(), -event.getY(), event.getEventTime(),
                    canStartDismissSwipe(event));
        }
        if (!canDismissDrawer()) mDismissSwipe.cancel();
        if (action == MotionEvent.ACTION_POINTER_DOWN) mDismissSwipe.cancel();
        if (action == MotionEvent.ACTION_MOVE
                && mDismissSwipe.move(event.getX(), -event.getY(),
                        event.getEventTime(), event.getPointerCount())) {
            if (!mDismissSwipeCaptured) {
                // RecyclerView may already disallow interception while it scrolls.
                // Observe dispatch, then cancel its stream exactly once when claimed.
                MotionEvent cancel = MotionEvent.obtain(event);
                cancel.setAction(MotionEvent.ACTION_CANCEL);
                super.dispatchTouchEvent(cancel);
                cancel.recycle();
                mDismissSwipeCaptured = true;
            }
        }
        if (mDismissSwipeCaptured) {
            if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
                boolean close = action == MotionEvent.ACTION_UP
                        && mDismissSwipe.end(event.getX(), -event.getY(), event.getPointerCount());
                mDismissSwipe.cancel();
                mDismissSwipeCaptured = false;
                if (close && canDismissDrawer()) {
                    post(new Runnable() {
                        @Override
                        public void run() {
                            if (canDismissDrawer()) mLauncher.showWorkspace(true);
                        }
                    });
                }
            }
            return true;
        }
        if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
            mDismissSwipe.cancel();
        }
        return super.dispatchTouchEvent(event);
    }

    @Override
    public boolean onInterceptTouchEvent(MotionEvent ev) {''')
path=APP+'src/com/android/launcher3/BaseContainerView.java'
edit(path,'''        mUseScrubber = SettingsProvider.getBoolean(context,
                SettingsProvider.SETTINGS_UI_USE_HORIZONTAL_SCRUBBER,
                R.bool.preferences_interface_use_horizontal_scrubber_default);''','''        // The modern Apps drawer has no alphabet footer; widget preferences remain native.
        mUseScrubber = getId() != R.id.apps_view && SettingsProvider.getBoolean(context,
                SettingsProvider.SETTINGS_UI_USE_HORIZONTAL_SCRUBBER,
                R.bool.preferences_interface_use_horizontal_scrubber_default);''')
path=APP+'res/values/colors.xml'
resource(path,'color','quantum_panel_bg_color_dark','#191C1A')
resource(path,'color','quantum_panel_bg_color','#F5F8F5')
for name in files:
    if name.endswith('.xml'):ET.parse(SRC/name)
print('Native top-of-list downward dismissal, Apps-only alphabet removal and continuous surface applied.')
