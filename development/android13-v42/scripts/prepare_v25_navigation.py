"""Apply device-specific input mapping and mutually exclusive navigation modes."""
from pathlib import Path
import difflib, subprocess, json
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
t=Path('/root/t110-build/lineage20')
e=p/'evidence/offline-v35';e.mkdir(exist_ok=True)
def patch(repo,filename,old,new,patchname):
    assert old!=new
    diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+filename if old else '/dev/null',tofile='b/'+filename))
    (p/'patches'/patchname).write_text(diff,encoding='utf-8')
    path=t/repo/filename;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(new,encoding='utf-8')
    return diff
helper='''package com.android.server.policy;

import android.view.KeyEvent;

/** Suppress only the T110's built-in navigation buttons, never its touch stream. */
final class T110NavigationKeys {
    static boolean shouldSuppress(boolean touchNavigation, String deviceName,
            boolean virtualDevice, int keyCode) {
        if (!touchNavigation || virtualDevice) return false;
        if (!"gpio-keys".equals(deviceName) && !"sec_touchscreen".equals(deviceName)) {
            return false;
        }
        return keyCode == KeyEvent.KEYCODE_HOME || keyCode == KeyEvent.KEYCODE_MOVE_HOME
                || keyCode == KeyEvent.KEYCODE_BACK || keyCode == KeyEvent.KEYCODE_MENU
                || keyCode == KeyEvent.KEYCODE_APP_SWITCH;
    }
}
'''
fn='services/core/java/com/android/server/policy/PhoneWindowManager.java'
old=(t/'frameworks/base'/fn).read_text()
anchor='''    public int interceptKeyBeforeQueueing(KeyEvent event, int policyFlags) {
        final int keyCode = event.getKeyCode();
'''
insert='''        // This board has no key-disable HAL. Filter its physical navigation
        // keys before wake/gesture handling while Lineage's touch navbar is on.
        // Virtual navbar events, external keyboards, power and volume pass through.
        if ("t110_bringup".equals(android.os.Build.DEVICE) && mForceNavbar == 1) {
            final InputDevice device = event.getDevice();
            if (device != null && T110NavigationKeys.shouldSuppress(true,
                    device.getName(), device.isVirtual(), keyCode)) {
                return 0;
            }
        }
'''
assert old.count(anchor)==1 and 'T110NavigationKeys.shouldSuppress' not in old
diff=patch('frameworks/base',fn,old,old.replace(anchor,anchor+insert),'0062-framework-t110-exclusive-navigation.patch')
helperfn='services/core/java/com/android/server/policy/T110NavigationKeys.java'
diff+=''.join(difflib.unified_diff([],helper.splitlines(True),fromfile='/dev/null',tofile='b/'+helperfn))
(p/'patches/0062-framework-t110-exclusive-navigation.patch').write_text(diff,encoding='utf-8')
(t/'frameworks/base'/helperfn).write_text(helper,encoding='utf-8')
fn='src/org/lineageos/lineageparts/input/ButtonSettings.java'
old=(t/'packages/apps/LineageParts'/fn).read_text()
anchor='''        return hardware.isSupported(LineageHardwareManager.FEATURE_KEY_DISABLE);'''
assert old.count(anchor)==1
new=old.replace(anchor,'''        // T110 implements key suppression in PhoneWindowManager instead of a HAL.
        return "t110_bringup".equals(android.os.Build.DEVICE)
                || hardware.isSupported(LineageHardwareManager.FEATURE_KEY_DISABLE);''')
patch('packages/apps/LineageParts',fn,old,new,'0063-lineageparts-t110-navigation-mode-switch.patch')
device=p/'work/device/samsung/t110_bringup'
for name,text in {'gpio-keys.kl':'key 102 HOME\nkey 114 VOLUME_DOWN\nkey 115 VOLUME_UP\n','sec_touchscreen.kl':'key 139 APP_SWITCH\nkey 158 BACK\n'}.items():
    f=device/'keylayout'/name;f.parent.mkdir(exist_ok=True);f.write_text(text,encoding='utf-8')
mk=device/'t110_system.mk';s=mk.read_text()
s+='''
# Board-specific navigation codes. Generic.kl treats Linux KEY_HOME as MOVE_HOME.
PRODUCT_COPY_FILES += \\
    $(LOCAL_PATH)/keylayout/gpio-keys.kl:$(TARGET_COPY_OUT_VENDOR)/usr/keylayout/gpio-keys.kl \\
    $(LOCAL_PATH)/keylayout/sec_touchscreen.kl:$(TARGET_COPY_OUT_VENDOR)/usr/keylayout/sec_touchscreen.kl
'''
mk.write_text(s,encoding='utf-8')
overlay=device/'overlay/lineage-sdk/lineage/res/res/values/config.xml'
assert not overlay.exists();overlay.parent.mkdir(parents=True,exist_ok=True)
overlay.write_text('''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <!-- Home (1), Back (2), Recents (16), Volume (64). Preserve volume options. -->
    <integer name="config_deviceHardwareKeys">83</integer>
    <integer name="config_deviceHardwareWakeKeys">65</integer>
</resources>
''',encoding='utf-8')
script=p/'scripts/build_system_image.sh';s=script.read_text();anchor="'frameworks/base:0060-systemui-shared-t110-software-task-snapshots.patch'; do"
assert s.count(anchor)==1
s=s.replace(anchor,"'frameworks/base:0060-systemui-shared-t110-software-task-snapshots.patch' 'frameworks/base:0062-framework-t110-exclusive-navigation.patch' 'packages/apps/LineageParts:0063-lineageparts-t110-navigation-mode-switch.patch'; do")
script.write_text(s,encoding='utf-8')
print('NAVIGATION_SOURCE_PREPARED')
