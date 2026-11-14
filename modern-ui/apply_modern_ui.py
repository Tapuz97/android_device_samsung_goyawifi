"""Native14.1 visual backport. Keeps the bring-up code and APIs in place."""
from pathlib import Path
import hashlib,json,re
SRC=Path('/root/t110-lineage14/android');WORK=Path('/root/t110-lineage14-ui')
assert (WORK/'baseline/project-manifest.json').is_file()
BEFORE=WORK/'before';BEFORE.mkdir(exist_ok=True)
index=WORK/'changed-files.json'
files=json.loads(index.read_text()) if index.is_file() else {}
def save(name,text):
    p=SRC/name
    if p.is_file() and p.read_bytes()==text.encode('utf-8'):
        return
    if name not in files:
        if p.exists():
            old=p.read_bytes();backup=BEFORE/name;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(old)
            files[name]={'before_sha256':hashlib.sha256(old).hexdigest()}
        else:files[name]={'before_sha256':None}
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    files[name]['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    index.write_text(json.dumps(files,indent=2)+'\n')
def read(name):return (SRC/name).read_text()
def edit(name,old,new):
    text=read(name)
    if new in text:
        return
    if old not in text:
        assert new in text,(name,old)
        return
    assert text.count(old)==1,(name,old)
    save(name,text.replace(old,new))
def resource(name,kind,key,value):
    text=read(name);pattern=rf'(<{kind} name="{re.escape(key)}">).*?(</{kind}>)'
    text,count=re.subn(pattern,lambda m:m[1]+value+m[2],text,flags=re.S)
    assert count==1,(name,key,count)
    save(name,text)
def xml(body):return '<?xml version="1.0" encoding="utf-8"?>\n'+body+'\n'
FW='frameworks/base/';UI=FW+'packages/SystemUI/';SET='packages/apps/Settings/';LAUNCH='packages/apps/Trebuchet/'

# DeviceDefault themes flow into native applications, popups and controls.
colors={'primary_device_default_dark':'#1B3028','primary_device_default_light':'#F5F8F5',
    'primary_device_default_settings':'#F5F8F5','primary_dark_device_default_dark':'#101B16',
    'primary_dark_device_default_light':'#EAF1EC','primary_dark_device_default_settings':'#EAF1EC',
    'accent_device_default_700':'#245B49','accent_device_default_light':'#326B57',
    'accent_device_default_dark':'#AFE5CE','accent_device_default_50':'#E0F4E9',
    'background_device_default_dark':'#151E19','background_device_default_light':'#F5F8F5',
    'background_floating_device_default_dark':'#26382E','background_floating_device_default_light':'#FAFCF9'}
for key,value in colors.items():resource(FW+'core/res/res/values/colors_device_defaults.xml','color',key,value)
edit(FW+'core/res/res/drawable/dialog_background_material.xml','android:radius="2dp"','android:radius="28dp"')
edit(FW+'core/res/res/drawable/popup_background_material.xml','android:radius="2dp"','android:radius="16dp"')

# Quick Settings uses the existing tile model, actions, policy checks and a11y.
save(UI+'res/values/t110_modern.xml',xml('''<resources>
    <color name="t110_qs_active">#AFE5CE</color>
    <color name="t110_qs_active_text">#0C3525</color>
    <color name="t110_qs_inactive">#2C3B33</color>
    <color name="t110_qs_inactive_text">#E5EFE8</color>
    <color name="t110_qs_disabled_text">#99B8C4BB</color>
</resources>'''))
save(UI+'res/drawable/t110_qs_tile_background.xml',xml('''<ripple xmlns:android="http://schemas.android.com/apk/res/android" android:color="#24FFFFFF">
    <item><selector>
        <item android:state_selected="true"><shape><solid android:color="@color/t110_qs_active"/><corners android:radius="36dp"/></shape></item>
        <item><shape><solid android:color="@color/t110_qs_inactive"/><corners android:radius="24dp"/></shape></item>
    </selector></item>
</ripple>'''))
base=UI+'src/com/android/systemui/qs/QSTileBaseView.java'
edit(base,'import android.view.View;','import android.view.View;\nimport android.view.ViewGroup;\nimport android.widget.ImageView;')
text=read(base)
start=text.index('    private Drawable newTileBackground() {');end=text.index('    private void setRipple(',start)
save(base,text[:start]+'''    private Drawable newTileBackground() {
        return mContext.getDrawable(R.drawable.t110_qs_tile_background);
    }

'''+text[end:])
text=read(base);start=text.index('    private void updateRippleSize(');end=text.index('    public void init(',start)
save(base,text[:start]+'''    private void updateRippleSize(int width, int height) {
        mRipple.setHotspotBounds(0, 0, width, height);
    }

    private void tintModernIcon(View view, int color) {
        if (view instanceof ImageView) {
            ((ImageView) view).setColorFilter(color);
        } else if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) {
                tintModernIcon(group.getChildAt(i), color);
            }
        }
    }

'''+text[end:])
edit(base,'        mIcon.setIcon(state);','''        mIcon.setIcon(state);
        boolean active = state instanceof QSTile.BooleanState
                && ((QSTile.BooleanState) state).value && !state.disabledByPolicy;
        setSelected(active);
        int foreground = mContext.getColor(state.disabledByPolicy
                ? R.color.t110_qs_disabled_text : active
                ? R.color.t110_qs_active_text : R.color.t110_qs_inactive_text);
        tintModernIcon(mIcon, foreground);''')
tile=UI+'src/com/android/systemui/qs/QSTileView.java'
edit(tile,'        setOrientation(VERTICAL);\n        setGravity(Gravity.CENTER);','''        setOrientation(HORIZONTAL);
        setGravity(Gravity.CENTER_VERTICAL);
        getIcon().setLayoutParams(new LayoutParams(res.getDimensionPixelSize(
                R.dimen.qs_tile_icon_size), LayoutParams.WRAP_CONTENT));''')
text=read(tile);start=text.index('        int padding = res.getDimensionPixelSize(R.dimen.qs_tile_padding_top);');end=text.index('        requestLayout();',start)
save(tile,text[:start]+'''        int horizontal = Math.round(16 * res.getDisplayMetrics().density);
        int vertical = Math.round(10 * res.getDisplayMetrics().density);
        setPaddingRelative(horizontal, vertical, horizontal, vertical);
'''+text[end:])
edit(tile,'        addView(view);','''        LayoutParams labelParams = new LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f);
        labelParams.setMarginStart(Math.round(12 * getResources().getDisplayMetrics().density));
        addView(view, labelParams);''')
edit(tile,'        mLabel.setEnabled(!state.disabledByPolicy);','''        mLabel.setEnabled(!state.disabledByPolicy);
        mLabel.setTextColor(mContext.getColor(state.disabledByPolicy
                ? R.color.t110_qs_disabled_text : isSelected()
                ? R.color.t110_qs_active_text : R.color.t110_qs_inactive_text));''')
save(UI+'res/layout/qs_tile_label.xml',xml('''<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="wrap_content" android:orientation="horizontal" android:gravity="center_vertical">
    <TextView android:id="@+id/tile_label" android:layout_width="0dp" android:layout_weight="1"
        android:layout_height="wrap_content" android:gravity="start|center_vertical" android:minLines="1" android:maxLines="2"
        android:ellipsize="end" android:textColor="@color/t110_qs_inactive_text" android:fontFamily="sans-serif-medium"
        android:textAppearance="@style/TextAppearance.QS.TileLabel" android:clickable="false"/>
    <ImageView android:id="@+id/restricted_padlock" android:layout_width="16dp" android:layout_height="16dp"
        android:layout_marginStart="4dp" android:src="@drawable/ic_info" android:scaleType="centerInside" android:visibility="gone"/>
</LinearLayout>'''))
for key,value in {'qs_tile_height':'76dp','qs_tile_margin':'8dp','qs_tile_margin_top':'8dp',
                  'qs_tile_icon_size':'28dp','qs_tile_text_size':'14sp','qs_tile_padding_below_icon':'0dp',
                  'qs_quick_tile_padding':'8dp','recents_task_view_rounded_corners_radius':'20dp',
                  'recents_task_view_shadow_rounded_corners_radius':'20dp'}.items():
    resource(UI+'res/values/dimens.xml','dimen',key,value)
for p in (SRC/UI/'res').glob('values*/config.xml'):
    relative=str(p.relative_to(SRC));text=p.read_text()
    if 'name="quick_settings_num_columns"' in text:resource(relative,'integer','quick_settings_num_columns','4' if 'land' in p.parent.name else '2')
    if 'name="quick_settings_num_rows"' in text:resource(relative,'integer','quick_settings_num_rows','2' if 'land' in p.parent.name else '3')
for key,value in {'system_bar_background_opaque':'#111B16','notification_panel_solid_background':'#111B16',
                  'notification_shade_background_color':'#111B16','recents_task_bar_default_background_color':'#EDF4EF',
                  'recents_task_view_default_background_color':'#F5F8F5'}.items():
    resource(UI+'res/values/colors.xml','color',key,value)
edit(UI+'res/drawable/qs_background_primary.xml','?android:attr/colorPrimary','#111B16')
for name in ('notification_material_bg.xml','notification_material_bg_dim.xml'):
    path=UI+'res/drawable/'+name;text=read(path)
    if '<corners ' not in text:save(path,text.replace('<shape>','<shape>\n            <corners android:radius="18dp"/>'))
edit(UI+'res/drawable/volume_dialog_background.xml','    <solid','    <corners android:radius="24dp"/>\n    <solid')

# Native Recents retains task dismissal and its localized Clear all label.
clear=UI+'res/layout/recents_stack_action_button.xml'
edit(clear,'android:textAllCaps="true"','android:textAllCaps="false"')
edit(clear,'android:textColor="#FFFFFF"','android:textColor="#0C3525"')
edit(clear,'android:shadowRadius="5"','android:shadowRadius="0"')
edit(clear,'android:layout_height="wrap_content"','android:layout_height="48dp"\n    android:gravity="center"\n    android:drawableStart="@drawable/ic_t110_clear_all"\n    android:drawablePadding="8dp"')
save(UI+'res/drawable/ic_t110_clear_all.xml',xml('''<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24"><path android:fillColor="#0C3525" android:pathData="M5,7h14v2H5zM3,11h14v2H3zM7,15h14v2H7z"/></vector>'''))
save(UI+'res/drawable/recents_stack_action_background.xml',xml('''<ripple xmlns:android="http://schemas.android.com/apk/res/android" android:color="#24326B57"><item><shape><solid android:color="#AFE5CE"/><corners android:radius="24dp"/></shape></item></ripple>'''))

# Settings' search field delegates to the EXISTING Settings search implementation.
edit(SET+'res/values/themes.xml','name="Theme.SettingsBase" parent="@android:style/Theme.DeviceDefault.Settings"',
     'name="Theme.SettingsBase" parent="@android:style/Theme.DeviceDefault.Light"')
edit(SET+'res/values/themes.xml','<style name="Theme.Settings" parent="Theme.SettingsBase">','''<style name="Theme.Settings" parent="Theme.SettingsBase">
        <item name="android:colorPrimary">#F5F8F5</item>
        <item name="android:colorPrimaryDark">#F5F8F5</item>
        <item name="android:colorAccent">#326B57</item>
        <item name="android:windowLightStatusBar">true</item>
        <item name="android:windowBackground">#F5F8F5</item>
        <item name="android:textColorPrimary">#17251E</item>
        <item name="android:textColorSecondary">#506258</item>
        <item name="android:colorControlNormal">#355446</item>
        <item name="android:listDivider">@android:color/transparent</item>''')
resource(SET+'res/values/colors.xml','color','card_background','#FFFFFF')
resource(SET+'res/values/colors.xml','color','card_background_grey','#EAF1EC')
for key,value in {'dashboard_padding_start':'16dp','dashboard_padding_end':'16dp',
    'dashboard_category_elevation':'0dp','dashboard_category_height':'48dp',
    'dashboard_category_title_margin_start':'12dp','dashboard_tile_minimum_height':'76dp',
    'dashboard_tile_image_size':'44dp','dashboard_tile_image_margin_start':'12dp',
    'dashboard_tile_image_margin_end':'16dp'}.items():resource(SET+'res/values/dimens.xml','dimen',key,value)
edit(SET+'res/layout/settings_main_dashboard.xml','@color/material_grey_300','#F5F8F5')
save(SET+'res/drawable/selectable_card.xml',xml('''<ripple xmlns:android="http://schemas.android.com/apk/res/android" android:color="?android:attr/colorControlHighlight"><item><shape><solid android:color="@color/card_background"/><corners android:radius="18dp"/></shape></item></ripple>'''))
save(SET+'res/drawable/t110_settings_icon_background.xml',xml('''<shape xmlns:android="http://schemas.android.com/apk/res/android"><solid android:color="#E2EFE6"/><corners android:radius="14dp"/></shape>'''))
edit(SET+'res/layout/dashboard_tile.xml','android:scaleType="centerInside"','''android:scaleType="centerInside"
        android:background="@drawable/t110_settings_icon_background"
        android:padding="8dp"''')
edit(SET+'res/layout/dashboard_tile.xml','android:minHeight="@dimen/dashboard_tile_minimum_height"','''android:minHeight="@dimen/dashboard_tile_minimum_height"
    android:layout_marginBottom="2dp"''')
edit(SET+'res/layout/dashboard_category.xml','android:background="@color/card_background"','android:background="@android:color/transparent"')
save(SET+'res/drawable/t110_search_background.xml',xml('''<ripple xmlns:android="http://schemas.android.com/apk/res/android" android:color="#18326B57"><item><shape><solid android:color="#E4EEE8"/><corners android:radius="24dp"/></shape></item></ripple>'''))
save(SET+'res/drawable/ic_t110_search.xml',xml('''<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="24dp" android:height="24dp" android:viewportWidth="24" android:viewportHeight="24"><path android:fillColor="#355446" android:pathData="M15.5,14h-0.79l-0.28,-0.27A6.471,6.471 0,0 0,16 9.5C16,5.91 13.09,3 9.5,3S3,5.91 3,9.5S5.91,16 9.5,16c1.61,0 3.09,-0.59 4.23,-1.57l0.27,0.28v0.79l5,4.99L20.49,19.49zM9.5,14C7.01,14 5,11.99 5,9.5S7.01,5 9.5,5S14,7.01 14,9.5S11.99,14 9.5,14z"/></vector>'''))
save(SET+'res/values/t110_modern.xml',xml('''<resources><string name="t110_search_settings">Search settings</string></resources>'''))
save(SET+'res/layout/dashboard.xml',xml('''<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android" android:layout_width="match_parent" android:layout_height="match_parent" android:orientation="vertical" android:background="#F5F8F5">
    <TextView android:id="@+id/t110_search_settings" android:layout_width="match_parent" android:layout_height="48dp"
        android:layout_marginStart="16dp" android:layout_marginEnd="16dp" android:layout_marginTop="8dp" android:layout_marginBottom="12dp"
        android:paddingStart="16dp" android:paddingEnd="16dp" android:gravity="center_vertical" android:background="@drawable/t110_search_background"
        android:drawableStart="@drawable/ic_t110_search" android:drawablePadding="12dp" android:text="@string/t110_search_settings" android:textColor="#355446"
        android:textSize="16sp" android:fontFamily="sans-serif" android:clickable="true" android:focusable="true"/>
    <com.android.settings.dashboard.conditional.FocusRecyclerView android:id="@+id/dashboard_container"
        android:layout_width="match_parent" android:layout_height="0dp" android:layout_weight="1" android:clipChildren="false"
        android:clipToPadding="false" android:focusable="false" android:paddingStart="@dimen/dashboard_padding_start"
        android:paddingEnd="@dimen/dashboard_padding_end" android:paddingTop="@dimen/dashboard_padding_top"
        android:paddingBottom="@dimen/dashboard_padding_bottom" android:scrollbars="vertical"/>
</LinearLayout>'''))
activity=SET+'src/com/android/settings/SettingsActivity.java'
edit(activity,'    @Override\n    public SharedPreferences getSharedPreferences(String name, int mode) {','''    public void startModernSearch() {
        if (mSearchMenuItem != null && mSearchView != null) {
            mSearchMenuItem.expandActionView();
            mSearchView.setIconified(false);
            mSearchView.requestFocus();
        } else {
            onSearchRequested();
        }
    }

    @Override
    public SharedPreferences getSharedPreferences(String name, int mode) {''')
edit(SET+'src/com/android/settings/dashboard/DashboardSummary.java',
    '        mDashboard = (FocusRecyclerView) view.findViewById(R.id.dashboard_container);','''        view.findViewById(R.id.t110_search_settings).setOnClickListener(v ->
                ((SettingsActivity) getActivity()).startModernSearch());
        mDashboard = (FocusRecyclerView) view.findViewById(R.id.dashboard_container);''')

# Launcher keeps its own icon-size and grid preferences, with a legible default.
resource(LAUNCH+'res/values/preferences_defaults.xml','bool','preferences_interface_general_icons_large_default','true')
for name in ('all_apps_search_bg.xml','folder_container.xml'):
    path=LAUNCH+'res/drawable/'+name;text=read(path)
    if '<corners' in text:
        save(path,re.sub(r'(<corners\s+android:radius=")[^"]+("\s*/>)',r'\g<1>24dp\2',text))

print(f'Applied native UI changes to {len(files)} source/resource files. Original14.1 images untouched; no tablet access.')
