"""Guard Settings' optional service lookups on the legacy T110 product."""
from pathlib import Path
import difflib, subprocess

p = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
t = Path('/root/t110-build/lineage20/packages/apps/Settings')
patch = p / 'patches/0069-settings-t110-optional-usb-ethernet.patch'
changes = {}

def edit(name, pairs):
    old = (t / name).read_text()
    new = old
    for before, after in pairs:
        assert before in new, (name, before)
        new = new.replace(before, after)
    changes[name] = old, new

base = 'src/com/android/settings/'
edit(base + 'network/EthernetTetherPreferenceController.java', [
    ('mEthernetManager = context.getSystemService(EthernetManager.class);',
     'mEthernetManager = getEthernetManager(context);'),
    ('    @OnLifecycleEvent(Lifecycle.Event.ON_START)', '''    public static EthernetManager getEthernetManager(Context context) {
        // The T110 product has no Ethernet service until its host stack is ported.
        // getSystemService itself reports a fatal WTF on this engineering build;
        // check the published binder before constructing a manager.
        if ("t110_bringup".equals(android.os.Build.DEVICE)
                && android.os.ServiceManager.checkService(Context.ETHERNET_SERVICE) == null) {
            return null;
        }
        return context.getSystemService(EthernetManager.class);
    }

    @OnLifecycleEvent(Lifecycle.Event.ON_START)''')])
for name in ['network/TetherEnabler.java', 'TetherSettings.java']:
    pairs = []
    for context in ['context', 'mContext']:
        old = context + '.getSystemService(EthernetManager.class)'
        if old in (t / (base + name)).read_text():
            pairs.append((old, 'com.android.settings.network.'
                          'EthernetTetherPreferenceController.getEthernetManager(' + context + ')'))
    edit(base + name, pairs)

edit(base + 'connecteddevice/usb/UsbBackend.java', [
    ('mUsbManager = context.getSystemService(UsbManager.class);',
     'mUsbManager = isServiceAvailable() ? context.getSystemService(UsbManager.class) : null;'),
    ('    public long getCurrentFunctions() {', '''    public static boolean isServiceAvailable() {
        // ADB uses the legacy gadget directly; that does not imply UsbService exists.
        return !"t110_bringup".equals(android.os.Build.DEVICE)
                || android.os.ServiceManager.checkService(Context.USB_SERVICE) != null;
    }

    public long getCurrentFunctions() {'''),
    ('return mUsbManager.getCurrentFunctions();',
     'return mUsbManager == null ? UsbManager.FUNCTION_NONE : mUsbManager.getCurrentFunctions();'),
    ('mUsbManager.setCurrentFunctions(functions);',
     'if (mUsbManager != null) mUsbManager.setCurrentFunctions(functions);'),
    ('return mUsbManager.getScreenUnlockedFunctions();',
     'return mUsbManager == null ? UsbManager.FUNCTION_NONE : mUsbManager.getScreenUnlockedFunctions();'),
    ('mUsbManager.setScreenUnlockedFunctions(functions);',
     'if (mUsbManager != null) mUsbManager.setScreenUnlockedFunctions(functions);'),
    ('    public boolean areFunctionsSupported(long functions) {',
     '    public boolean areFunctionsSupported(long functions) {\n        if (mUsbManager == null) return false;'),
    ('        List<UsbPort> ports = mUsbManager.getPorts();',
     '        if (mUsbManager == null) return;\n        List<UsbPort> ports = mUsbManager.getPorts();')])
edit(base + 'connecteddevice/usb/UsbDetailsFragment.java', [
    ('                    return checkIfUsbDataSignalingIsDisabled(',
     '                    return UsbBackend.isServiceAvailable() && checkIfUsbDataSignalingIsDisabled(')])

assert not patch.exists()
patch.write_text(''.join(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
    fromfile='a/' + name, tofile='b/' + name)) for name, (old, new) in changes.items()))
subprocess.run(['git', 'apply', '--check', str(patch)], cwd=t, check=True)
subprocess.run(['git', 'apply', str(patch)], cwd=t, check=True)
build = p / 'scripts/build_system_image.sh'
s = build.read_text()
anchor = "'packages/apps/Trebuchet:0068-trebuchet-t110-software-surface-transactions.patch'"
assert s.count(anchor) == 1
build.write_text(s.replace(anchor, anchor + " 'packages/apps/Settings:0069-settings-t110-optional-usb-ethernet.patch'"))
print('SETTINGS_OPTIONAL_SERVICES_PATCH_APPLIED')
