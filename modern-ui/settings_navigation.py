"""Consolidate native navigation settings and replace the legacy settings drawer."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
helper=Path(__file__).with_name('apply_modern_ui.py').read_text()
exec(helper[:helper.index("FW='frameworks/base/'")])
SET='packages/apps/Settings/'
PART='packages/apps/CMParts/'
LIB='frameworks/base/packages/SettingsLib/'

# Reuse the platform's native, auto-mirrored Material Back asset.
back=read('frameworks/base/core/res/res/drawable/ic_ab_back_material.xml')
back=back.replace('?attr/colorControlNormal','?android:attr/colorControlNormal')
back=back.replace('@color/white','@android:color/white')
save(LIB+'res/drawable/t110_nav_back.xml',back)
path=LIB+'src/com/android/settingslib/drawer/SettingsDrawerActivity.java'
edit(path,'''        if (mDrawerLayout == null) {
            return;
        }
        Toolbar toolbar''','''        if (mDrawerLayout == null) {
            return;
        }
        mDrawerLayout.setDrawerLockMode(DrawerLayout.LOCK_MODE_LOCKED_CLOSED);
        Toolbar toolbar''')
edit(path,'''    public boolean onOptionsItemSelected(MenuItem item) {
        if (mShowingMenu''','''    public boolean onOptionsItemSelected(MenuItem item) {
        if (!mShowingMenu && item.getItemId() == android.R.id.home) {
            onBackPressed();
            return true;
        }
        if (mShowingMenu''')
edit(path,'''        if (mDrawerLayout != null) {
            mDrawerLayout.openDrawer(Gravity.START);''','''        if (mDrawerLayout != null && mShowingMenu) {
            mDrawerLayout.openDrawer(Gravity.START);''')
edit(path,'''        if (mDrawerAdapter.getCount() != 0) {
            mDrawerLayout.setDrawerLockMode(DrawerLayout.LOCK_MODE_UNLOCKED);
        } else {
            mDrawerLayout.setDrawerLockMode(DrawerLayout.LOCK_MODE_LOCKED_CLOSED);
        }''','''        // Keep native category/package updates, but disable the obsolete side drawer.
        mDrawerLayout.setDrawerLockMode(DrawerLayout.LOCK_MODE_LOCKED_CLOSED);''')
old=read(path)
start=old.index('    public void showMenuIcon() {')
end=old.index('    public List<DashboardCategory> getDashboardCategories()',start)
save(path,old[:start]+'''    public void showMenuIcon() {
        // Retain this shared API for clients; category navigation now means Back.
        mShowingMenu = false;
        if (mDrawerLayout != null) {
            mDrawerLayout.setDrawerLockMode(DrawerLayout.LOCK_MODE_LOCKED_CLOSED);
        }
        if (getActionBar() != null) {
            getActionBar().setHomeAsUpIndicator(R.drawable.t110_nav_back);
            getActionBar().setHomeActionContentDescription(
                    com.android.internal.R.string.action_bar_up_description);
            getActionBar().setDisplayHomeAsUpEnabled(true);
            getActionBar().setHomeButtonEnabled(true);
        }
    }

'''+old[end:])

path=SET+'src/com/android/settings/SettingsActivity.java'
edit(path,'''        mActionBar = getActionBar();
        if (mActionBar != null) {
            mActionBar.setDisplayHomeAsUpEnabled(mDisplayHomeAsUpEnabled);
            mActionBar.setHomeButtonEnabled(mDisplayHomeAsUpEnabled);
        }''','''        mActionBar = getActionBar();
        updateSettingsNavigation();''')
edit(path,'''    public void onBackStackChanged() {
        setTitleFromBackStack();
    }''','''    public void onBackStackChanged() {
        setTitleFromBackStack();
        updateSettingsNavigation();
    }

    @Override
    public void showMenuIcon() {
        updateSettingsNavigation();
    }

    private void updateSettingsNavigation() {
        mDisplayHomeAsUpEnabled = !mIsShowingDashboard || mSearchMenuItemExpanded
                || getFragmentManager().getBackStackEntryCount() > 0;
        if (getActionBar() == null) return;
        if (mDisplayHomeAsUpEnabled) {
            super.showMenuIcon();
        } else {
            getActionBar().setDisplayHomeAsUpEnabled(false);
            getActionBar().setHomeButtonEnabled(false);
        }
    }''')
edit(path,'''        if (super.onOptionsItemSelected(item)) {
            return true;
        }
        if (mDisplayHomeAsUpEnabled && item.getItemId() == android.R.id.home) {
            finish();
            return true;
        }
        return false;''','''        if (mDisplayHomeAsUpEnabled && item.getItemId() == android.R.id.home) {
            onBackPressed();
            return true;
        }
        return super.onOptionsItemSelected(item);''')
edit(path,'        mSearchView = (SearchView) mSearchMenuItem.getActionView();',
     '        mSearchView = mSearchMenuItem == null ? null : (SearchView) mSearchMenuItem.getActionView();')
path=SET+'res/menu/options_menu.xml'
save(path,read(path).replace('collapseActionView|ifRoom','collapseActionView|always'))
# Remove the duplicate search row; retain the native expandable toolbar SearchView.
path=SET+'res/layout/dashboard.xml'
text=read(path)
text,count=re.subn(r'    <TextView android:id="@\+id/t110_search_settings".*?/>\n',
                   '',text,flags=re.S)
if count:save(path,text)
else:
    assert 't110_search_settings' not in text
path=SET+'src/com/android/settings/dashboard/DashboardSummary.java'
text=read(path)
text,count=re.subn(r'        view\.findViewById\(R\.id\.t110_search_settings\)\.setOnClickListener\(.*?\n                \}\);\n',
                   '',text,flags=re.S)
if count:save(path,text)
else:assert 'R.id.t110_search_settings' not in text

# Keep the proven native hardware/navigation controls as the parent page.
save(PART+'res/values/t110_navigation.xml',xml('''<resources>
    <string name="t110_gestures_navigation_title">Gestures &amp; Navigation</string>
    <string name="t110_system_gestures_title">Gestures</string>
    <string name="t110_system_gestures_summary">Power-button shortcuts and screen gestures</string>
</resources>'''))
for path in (PART+'res/xml/parts_catalog.xml',PART+'res/xml/button_settings.xml',PART+'AndroidManifest.xml'):
    save(path,read(path).replace('@string/button_pref_title','@string/t110_gestures_navigation_title'))
path=PART+'res/xml/button_settings.xml'
gesture_section='''    <PreferenceCategory android:title="@string/t110_system_gestures_title">
        <Preference android:key="t110_system_gestures"
            android:title="@string/t110_system_gestures_title"
            android:summary="@string/t110_system_gestures_summary">
            <intent android:action="android.intent.action.MAIN"
                android:targetPackage="com.android.settings"
                android:targetClass="com.android.settings.Settings$GestureSettingsActivity" />
        </Preference>
    </PreferenceCategory>
</PreferenceScreen>'''
if 'android:key="t110_system_gestures"' not in read(path):
    head,tail=read(path).rsplit('</PreferenceScreen>',1)
    save(path,head+gesture_section+tail)
path=PART+'src/org/cyanogenmod/cmparts/PartsActivity.java'
save(path,read(path).replace('                mHomeAsUp = false;',
                            '                mHomeAsUp = true;'))

# One dashboard category. Preserve the existing gesture activity/search deep links.
path=SET+'AndroidManifest.xml'
text=read(path);start=text.index('        <activity android:name="Settings$GestureSettingsActivity"')
end=text.index('        </activity>',start)+len('        </activity>')
activity=text[start:end]
activity=activity.replace('android:enabled="@bool/config_gesture_settings_enabled"','android:enabled="true"')
activity=activity.replace('''            <intent-filter>
                <action android:name="com.android.settings.action.SETTINGS" />
            </intent-filter>
''','')
save(path,text[:start]+activity+text[end:])
for name in files:
    if name.endswith('.xml'):ET.parse(SRC/name)
print('One Gestures & Navigation category, native category Back, toolbar-only search applied.')
