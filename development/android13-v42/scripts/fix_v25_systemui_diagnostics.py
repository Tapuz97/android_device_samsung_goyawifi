from pathlib import Path
import difflib
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');t=Path('/root/t110-build/lineage20')
name='packages/SystemUI/src/com/android/systemui/DejankUtils.java';f=t/'frameworks/base'/name
old=f.read_text();anchor='''    public static final boolean STRICT_MODE_ENABLED = Build.IS_ENG
            || SystemProperties.getBoolean("persist.sysui.strictmode", false);'''
assert old.count(anchor)==1
new=old.replace(anchor,'''    // Respect the system diagnostic opt-out on engineering devices. An explicit
    // SystemUI override can still enable diagnostics when a developer needs them.
    public static final boolean STRICT_MODE_ENABLED = SystemProperties.getBoolean(
            "persist.sysui.strictmode", Build.IS_ENG
                    && !SystemProperties.getBoolean(StrictMode.DISABLE_PROPERTY, false));''')
f.write_text(new,encoding='utf-8')
(p/'patches/0066-systemui-respect-strictmode-default-optout.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+name,tofile='b/'+name)),encoding='utf-8')
f=p/'scripts/build_system_image.sh';s=f.read_text();anchor="'packages/apps/LineageParts:0063-lineageparts-t110-navigation-mode-switch.patch'; do"
assert s.count(anchor)==1
s=s.replace(anchor,"'packages/apps/LineageParts:0063-lineageparts-t110-navigation-mode-switch.patch' 'frameworks/base:0066-systemui-respect-strictmode-default-optout.patch'; do")
f.write_text(s,encoding='utf-8')
print('SYSTEMUI_DIAGNOSTICS_CORRECTED')
