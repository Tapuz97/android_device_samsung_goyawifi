"""Inspect actual-image navigation resources, intents, controls and fade config."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,xml.etree.ElementTree as ET
WORK=Path('/root/t110-lineage14-ui');SRC=Path('/root/t110-lineage14/android')
ART=WORK/'artifacts-settings-lock-20261115'
DEST=ART/'settings-verification';DEST.mkdir(exist_ok=True)
A='{http://schemas.android.com/apk/res/android}'
aapt=WORK/'out/host/linux-x86/bin/aapt'
# Reuse the compiled-manifest parser without running the icon checker's main loop.
tree=ast.parse(Path(__file__).with_name('verify_native_icons.py').read_text())
parser=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parsed_manifest')
exec(compile(ast.Module(body=[parser],type_ignores=[]),'<manifest-parser>','exec'))
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(8*1024*1024),b''):h.update(data)
    return h.hexdigest()
def extract(rel,name):
    p=DEST/name
    subprocess.run(['debugfs','-R','dump -p /'+rel+' '+str(p),str(ART/'system.raw.img')],
                   check=True,capture_output=True)
    assert p.is_file() and digest(p)==digest(WORK/'out/target/product/goyawifi/system'/rel),rel
    return p
def dump(apk,what,path=None):
    args=[str(aapt),'dump',what,str(apk)]
    if what=='resources':args=[str(aapt),'dump','--values','resources',str(apk)]
    if path:args.append(path)
    return subprocess.check_output(args,text=True)
settings=extract('priv-app/Settings/Settings.apk','Settings.apk')
parts=extract('priv-app/CMParts/CMParts.apk','CMParts.apk')
framework=extract('framework/framework-res.apk','framework-res.apk')
services=extract('framework/oat/arm/services.odex','services.odex')
def app_manifest(apk):
    root=parsed_manifest(dump(apk,'xmltree','AndroidManifest.xml'))
    return next(n for n in root['children'] if n['tag']=='application')
def actions(component):
    return {n['attrs'].get('android:name') for i in component['children']
            if i['tag']=='intent-filter' for n in i['children'] if n['tag']=='action'}
parts_app=app_manifest(parts)
button=next(n for n in parts_app['children'] if n['tag']=='activity-alias'
            and n['attrs']['android:name'].endswith('.input.ButtonSettings'))
assert 'com.android.settings.action.EXTRA_SETTINGS' in actions(button)
resources=dump(parts,'resources')
title_ids=set(re.findall(r'resource\s+(0x[0-9a-f]+)\s+\S+:string/t110_gestures_navigation_title\b',resources))
assert len(title_ids)==1 and button['attrs']['android:label']=='@'+next(iter(title_ids))
assert '"Gestures & Navigation"' in resources
parts_catalog=dump(parts,'xmltree','res/xml/parts_catalog.xml')
assert 'button_settings' in parts_catalog and '=@'+next(iter(title_ids)) in parts_catalog
settings_app=app_manifest(settings)
gestures=next(n for n in settings_app['children'] if n['tag']=='activity'
              and n['attrs']['android:name'].endswith('Settings$GestureSettingsActivity'))
assert 'com.android.settings.action.SETTINGS' not in actions(gestures)
assert 'android.intent.action.MAIN' in actions(gestures)
assert gestures['attrs']['android:enabled']=='(type 0x12)0xffffffff'
button_xml=dump(parts,'xmltree','res/xml/button_settings.xml')
assert 'com.android.settings.Settings$GestureSettingsActivity' in button_xml
before=WORK/'before/packages/apps/CMParts/res/xml/button_settings.xml'
old_keys={e.get(A+'key') for e in ET.parse(before).iter() if e.get(A+'key')}
for key in old_keys:
    if not key.startswith('@'):assert '"'+key+'"' in button_xml,key
menu=dump(settings,'xmltree','res/menu/options_menu.xml')
assert re.search(r'android:showAsAction.*0xa\b',menu),menu
dashboard=dump(settings,'xmltree','res/layout/dashboard.xml')
assert 'E: TextView' not in dashboard
assert 'FocusRecyclerView' in dashboard
for apk in (settings,parts):
    arrow=dump(apk,'xmltree','res/drawable/t110_nav_back.xml')
    assert 'E: vector' in arrow and 'android:autoMirrored' in arrow
config=dump(framework,'resources')
assert re.search(r'resource\s+0x[0-9a-f]+\s+android:bool/config_animateScreenLights:.*d=0xffffffff',config)
report={'status':'PASS_SETTINGS_NAVIGATION_AND_LOCK_IMAGE_CHECKS',
    'system_image_sha256':digest(ART/'system.raw.img'),
    'one_dashboard_navigation_category':True,'native_button_preference_keys_preserved':len(old_keys),
    'existing_gesture_activity_enabled_and_nested':True,
    'native_back_asset_in_settings_and_cmparts':True,'toolbar_search_always_visible':True,
    'duplicate_dashboard_search_row_removed':True,'native_dim_fade_selected':True,
    'services_odex_sha256':digest(services),'runtime_navigation_and_lock_checks':'PENDING'}
(ART/'settings-lock-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
