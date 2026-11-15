"""Bounded native-screen and launcher gesture checks; no continuous feed."""
from pathlib import Path
import json, re, subprocess, time, xml.etree.ElementTree as ET
from PIL import Image
ADB=r'C:\Users\Gal\AppData\Local\Android\Sdk\platform-tools\adb.exe'
SERIAL='3004523270272200'
DEST=Path(__file__).parent.parent/'tests/swipe-up-20261115'
DEST.mkdir(parents=True,exist_ok=True)

def adb(*args, timeout=40):
    p=subprocess.run([ADB,'-s',SERIAL,*args],capture_output=True,timeout=timeout)
    assert p.returncode==0,p.stderr.decode(errors='replace')[-500:]
    return p.stdout

def shell(s):
    return adb('shell',s).decode(errors='replace').replace('\r','')

def snapshot(name):
    png=DEST/(name+'.png')
    png.write_bytes(adb('exec-out','screencap -p 2>/dev/null'))
    with Image.open(png) as frame:
        assert frame.width>0 and frame.height>0
    shell('uiautomator dump /data/local/tmp/t110-swipe-window.xml')
    xml=adb('exec-out','cat /data/local/tmp/t110-swipe-window.xml')
    (DEST/(name+'.xml')).write_bytes(xml)
    return ET.fromstring(xml)

assert shell('getprop sys.boot_completed').strip()=='1'
assert '/system/priv-app/Trebuchet' in shell('pm path com.cyanogenmod.trebuchet')
shell('input keyevent 224; input keyevent 82; input keyevent 3')
time.sleep(2)
home=snapshot('home-before')
nodes=list(home.iter('node'))
if not any(n.get('package')=='com.cyanogenmod.trebuchet' for n in nodes):
    # This build's nonsecure swipe keyguard ignores KEYCODE_MENU. A normal
    # upward unlock gesture does not dismiss a PIN/password challenge.
    assert any(n.get('resource-id','').endswith('/lock_icon') for n in nodes)
    root_bounds=list(map(int,re.findall(r'\d+',nodes[0].get('bounds'))))
    unlock_x=(root_bounds[0]+root_bounds[2])//2
    shell('input swipe %d %d %d %d 450'%(unlock_x,root_bounds[3]-130,
          unlock_x,root_bounds[1]+180))
    time.sleep(2)
    shell('input keyevent 3')
    time.sleep(1)
    home=snapshot('home-before')
    nodes=list(home.iter('node'))
assert any(n.get('package')=='com.cyanogenmod.trebuchet' for n in nodes)
assert not any(n.get('resource-id','').endswith('/all_apps_button')
               or n.get('content-desc')=='Apps' for n in nodes)
bounds=nodes[0].get('bounds')
nums=list(map(int,re.findall(r'\d+',bounds)))
assert len(nums)==4,bounds
left,top,right,bottom=nums
x=int(left+(right-left)*0.52)
start=int(top+(bottom-top)*0.70)
end=int(top+(bottom-top)*0.28)
shell('input swipe %d %d %d %d 350'%(x,start,x,end))
time.sleep(2)
drawer=snapshot('drawer-after-swipe')
ids=[n.get('resource-id','') for n in drawer.iter('node')]
assert any(n.endswith('/apps_view') or n.endswith('/apps_list_view')
           or n.endswith('/search_box_container') for n in ids),ids
shell('input keyevent 4')
time.sleep(1)
returned=snapshot('home-after-back')
assert not any(n.get('resource-id','').endswith('/all_apps_button')
               or n.get('content-desc')=='Apps'
               for n in returned.iter('node'))
assert not any(n.get('resource-id','').endswith('/apps_list_view')
               for n in returned.iter('node')),'Back did not close the drawer'
crashes=shell('logcat -b crash -d -t 80')
(DEST/'crash-buffer-PRIVATE.txt').write_text(crashes,encoding='utf-8')
report={'status':'AUTOMATED_NATIVE_SCREEN_CHECKS_PASSED_PHYSICAL_TOUCH_PENDING',
    'swipe_opens_native_drawer':True,'back_returns_home':True,
    'drawer_button_not_visible_before_after':True,
    'new_java_crash_in_snapshot':'FATAL EXCEPTION' in crashes,
    'physical_finger_gesture_checked':False,'continuous_capture_running':False}
(DEST/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
