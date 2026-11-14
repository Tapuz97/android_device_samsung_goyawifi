"""Finish the API25 native visual backport; never contacts the tablet."""
from pathlib import Path
import hashlib,json,re,urllib.request,xml.etree.ElementTree as ET

helper=Path(__file__).with_name('apply_modern_ui.py').read_text()
exec(helper[:helper.index("FW='frameworks/base/'")])
FW='frameworks/base/';UI=FW+'packages/SystemUI/';SET='packages/apps/Settings/'
LAUNCH='packages/apps/Trebuchet/';PICK='packages/apps/WallpaperPicker/'

# Avoid introducing Java8 requirements into Settings' Java7 source target.
edit(SET+'src/com/android/settings/dashboard/DashboardSummary.java',
'''        view.findViewById(R.id.t110_search_settings).setOnClickListener(v ->
                ((SettingsActivity) getActivity()).startModernSearch());''',
'''        view.findViewById(R.id.t110_search_settings).setOnClickListener(
                new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {
                        ((SettingsActivity) getActivity()).startModernSearch();
                    }
                });''')

# Honor each native parent theme's foreground contract. Plain Light uses dark
# icons; Settings/DarkActionBar variants use light icons. Main Settings has
# its own explicit light-surface override.
resource(FW+'core/res/res/values/colors_device_defaults.xml','color','primary_device_default_light','#F5F8F5')
resource(FW+'core/res/res/values/colors_device_defaults.xml','color','primary_dark_device_default_light','#EAF1EC')
resource(FW+'core/res/res/values/colors_device_defaults.xml','color','primary_device_default_settings','#1B3028')
resource(FW+'core/res/res/values/colors_device_defaults.xml','color','primary_dark_device_default_settings','#101B16')
edit(SET+'res/values/themes.xml','@*android:drawable/ic_menu_moreoverflow_holo_dark',
     '@*android:drawable/ic_menu_moreoverflow_material')

# Native power actions keep all existing IDs, listeners and advanced restart.
path=FW+'core/res/res/layout/global_actions_item.xml'
resource_path=FW+'core/res/res/drawable/t110_power_icon_background.xml'
save(resource_path,xml('''<shape xmlns:android="http://schemas.android.com/apk/res/android"><solid android:color="#20326B57"/><corners android:radius="24dp"/></shape>'''))
edit(path,'android:minHeight="?android:attr/listPreferredItemHeight"','android:minHeight="72dp"')
edit(path,'android:layout_width="56dp"\n        android:layout_height="56dp"',
     '''android:layout_width="48dp"
        android:layout_height="48dp"
        android:background="@drawable/t110_power_icon_background"''')

# A stronger single-line lock clock fits landscape and retains locale/12-24h,
# weather, lock security and all native notification placement.
path=FW+'packages/Keyguard/res/values/styles.xml'
text=read(path)
start=text.index('    <style name="widget_big_thin">');end=text.index('</style>',start)
block=text[start:end].replace('sans-serif-light','sans-serif-medium')
save(path,text[:start]+block+text[end:])

# Launcher surfaces retain its existing inset/padding contract.
save(LAUNCH+'res/drawable/quantum_panel.xml',xml('''<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="#F5F8F5"/><corners android:radius="24dp"/>
    <padding android:left="8dp" android:top="8dp" android:right="8dp" android:bottom="8dp"/>
</shape>'''))
save(LAUNCH+'res/drawable/quantum_panel_dark.xml',xml('''<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="#26382E"/><corners android:radius="24dp"/>
    <padding android:left="8dp" android:top="8dp" android:right="8dp" android:bottom="8dp"/>
</shape>'''))
for name in ('quantum_panel_shape.xml','quantum_panel_shape_dark.xml'):
    edit(LAUNCH+'res/drawable/'+name,'android:radius="2dp"','android:radius="24dp"')
for key,value in {'quantum_panel_text_color':'#17251E',
    'quantum_panel_text_color_dark':'#E5EFE8','quantum_panel_bg_color':'#F5F8F5',
    'quantum_panel_bg_color_dark':'#1B3028'}.items():
    resource(LAUNCH+'res/values/colors.xml','color',key,value)

# Pin official artwork and its upstream license. No third-party wallpaper app.
pin='5a1814d916321aecb72d60d13b5e52bc719251bd'
repo='https://raw.githubusercontent.com/LineageOS/android_vendor_lineage/'+pin+'/'
reference=WORK/'reference';reference.mkdir(exist_ok=True)
license_data=urllib.request.urlopen(repo+'LICENSE',timeout=60).read()
assert b'Apache License' in license_data
(reference/'vendor-lineage-LICENSE').write_bytes(license_data)
art='overlay/common/frameworks/base/core/res/res/'
assets=[]
for qualifier,name in [('drawable-sw720dp-nodpi','lineage_current.png'),('drawable-hdpi','lineage_current_small.png')]:
    url=repo+art+qualifier+'/default_wallpaper.png'
    data=urllib.request.urlopen(url,timeout=60).read()
    assert data.startswith(b'\x89PNG\r\n\x1a\n')
    path=PICK+'res/drawable-nodpi/'+name
    target=SRC/path
    if path not in files:
        assert not target.exists()
        files[path]={'before_sha256':None}
    target.write_bytes(data)
    files[path]['sha256']=hashlib.sha256(data).hexdigest()
    index.write_text(json.dumps(files,indent=2)+'\n')
    assets.append({'source':url,'file':path,'sha256':files[path]['sha256']})
edit(PICK+'res/values-nodpi/wallpapers.xml','        <item>arc</item>',
     '        <item>lineage_current</item>\n        <item>arc</item>')
(reference/'upstream.json').write_text(json.dumps({
    'frameworks_base':{'branch':'lineage-24.0','commit':'4b252a1f5f128f24ea29b03457e8f903a6f19740'},
    'settings':{'branch':'lineage-24.0','commit':'31b1a9f1cab9638bc6af9f4e6412fbf3b3a7947a'},
    'artwork_commit':pin,'assets':assets,
    'scope':'Visual backport to native API25 views; no newer Android APIs or dynamic color engine.'
},indent=2)+'\n')

errors=[]
for name in files:
    if name.endswith('.xml'):
        try:ET.parse(SRC/name)
        except ET.ParseError as e:errors.append((name,str(e)))
assert not errors,errors
print('Complete: %d tracked files; changed XML is well formed; official wallpaper added to native picker.'%len(files))
