"""Bounded real-device settings flows and one native dim-fade sleep/wake check."""
from pathlib import Path
import atexit,json,re,subprocess,time,xml.etree.ElementTree as ET
ADB=r'C:\Users\Gal\AppData\Local\Android\Sdk\platform-tools\adb.exe'
BASE=[ADB,'-s','3004523270272200']
DEST=Path(__file__).parent.parent/'tests/settings-navigation-20261115'
DEST.mkdir(parents=True,exist_ok=True)
def adb(*args,timeout=45):
    p=subprocess.run(BASE+list(args),capture_output=True,timeout=timeout)
    assert p.returncode==0,p.stderr.decode(errors='replace')[-300:]
    return p.stdout
def shell(command):return adb('shell',command).decode(errors='replace').replace('\r','')
def hierarchy():
    shell('uiautomator dump /data/local/tmp/t110-settings-nav.xml')
    return ET.fromstring(adb('exec-out','cat /data/local/tmp/t110-settings-nav.xml'))
def snapshot(name):
    png=adb('exec-out','screencap -p 2>/dev/null')
    assert png.startswith(b'\x89PNG\r\n\x1a\n')
    (DEST/(name+'.png')).write_bytes(png)
    root=hierarchy()
    ET.ElementTree(root).write(DEST/(name+'.xml'),encoding='utf-8',xml_declaration=True)
    return root
def point(n):
    x,y,r,b=map(int,re.findall(r'\d+',n.get('bounds')))
    return (x+r)//2,(y+b)//2
def tap(n):shell('input tap %d %d'%point(n));time.sleep(1)
def row(root,text):
    parents={child:parent for parent in root.iter() for child in parent}
    for n in root.iter('node'):
        if n.get('text')!=text:continue
        target=n
        while target is not None:
            if any(t in target.get('class','') for t in ('ListView','RecyclerView','ScrollView')):
                target=None
                break
            if target.get('clickable')=='true':break
            target=parents.get(target)
        if target is not None:return target
    return None
def back(root):
    n=next((n for n in root.iter('node') if n.get('content-desc')=='Navigate up'),None)
    assert n is not None,'Native Back missing'
    assert not any(n.get('content-desc')=='Open navigation drawer' for n in root.iter('node'))
    tap(n)
def title(root,name):
    return any(n.get('text')==name for n in root.iter('node'))
def find_scrolling(text,root):
    for _ in range(8):
        found=row(root,text)
        if found is not None:return found,root
        shell('input swipe 300 850 300 330 350');time.sleep(.5)
        root=hierarchy()
    raise AssertionError('Preference not found: '+text)
def wake_unlock():
    shell('input keyevent 224');time.sleep(1)
    shell('input swipe 300 970 300 180 500');time.sleep(1)
assert shell('getprop sys.boot_completed').strip()=='1'
old_timeout=shell('settings get system screen_off_timeout').strip()
assert old_timeout.isdigit()
atexit.register(lambda:shell('settings put system screen_off_timeout '+old_timeout))
shell('settings put system screen_off_timeout 180000')
wake_unlock()
shell('am start -W -a android.settings.SETTINGS');time.sleep(1)
root=snapshot('after-root')
if not title(root,'Settings'):
    wake_unlock();shell('am start -W -a android.settings.SETTINGS');root=snapshot('after-root')
assert title(root,'Settings')
assert not any(n.get('resource-id','').endswith('/t110_search_settings') for n in root.iter('node'))
search=next(n for n in root.iter('node') if n.get('resource-id','').endswith('/search'))
heading=next(n for n in root.iter('node') if n.get('text')=='Settings')
assert point(search)[0]>point(heading)[0] and abs(point(search)[1]-point(heading)[1])<25
display,root=find_scrolling('Display',root);tap(display)
display_root=snapshot('after-display')
assert title(display_root,'Display')
back(display_root);root=hierarchy()
assert title(root,'Settings')
navigation,root=find_scrolling('Gestures & Navigation',root)
assert not title(root,'Buttons')
tap(navigation);navigation_root=snapshot('after-navigation')
assert title(navigation_root,'Gestures & Navigation')
gesture,navigation_root=find_scrolling('Gestures',navigation_root)
tap(gesture);gesture_root=snapshot('after-gestures')
assert title(gesture_root,'Gestures')
back(gesture_root);navigation_root=hierarchy()
assert title(navigation_root,'Gestures & Navigation')
back(navigation_root);root=hierarchy()
assert title(root,'Settings')
search=next(n for n in root.iter('node') if n.get('resource-id','').endswith('/search'))
tap(search)
shell('input text navigation');time.sleep(3)
results=snapshot('after-search')
matches=[n for n in results.iter('node') if 'navigation' in n.get('text','').lower()
         and n.get('class')!='android.widget.EditText']
assert matches,'Native search returned no navigation results'
# Leave native search cleanly before the explicit screen-off check.
shell('input keyevent 4; input keyevent 4')
shell('input keyevent 223');time.sleep(2)
display_dump=shell('dumpsys display')
(DEST/'sleep-display-PRIVATE.txt').write_text(display_dump,encoding='utf-8')
assert 'mColorFadeFadesConfig=true' in display_dump
assert re.search(r'mMode=2\b',display_dump),'Dim-layer mode was not selected'
power=shell('dumpsys power')
assert 'mWakefulness=Asleep' in power
wake_unlock();shell('am start -W -a android.settings.SETTINGS')
root=snapshot('after-wake')
assert title(root,'Settings')
crash=shell('logcat -b crash -d -t 80')
(DEST/'crash-buffer-PRIVATE.txt').write_text(crash,encoding='utf-8')
assert 'FATAL EXCEPTION' not in crash
result={'status':'AUTOMATED_SETTINGS_AND_LOCK_CHECKS_PASSED_PHYSICAL_LOCK_PENDING',
    'single_gestures_navigation_category':True,'display_category_back_returns_root':True,
    'native_gestures_nested_and_back_returns_parent':True,'toolbar_search_inline_right_of_title':True,
    'native_search_returns_navigation_results':True,'no_duplicate_search_row':True,
    'dim_fade_selected_at_sleep':True,'sleep_and_wake_to_settings':True,
    'new_java_crash':False,'continuous_capture_running':False,
    'physical_lock_animation_confirmed':False}
(DEST/'acceptance.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
