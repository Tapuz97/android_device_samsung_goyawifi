"""Apply and archive the narrowly opted-in synchronous Android 13 USB backend."""
import difflib
import subprocess
from pathlib import Path
root = Path('/root/t110-build/lineage20/packages/modules/adb')
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
path = root / 'daemon/usb.cpp'
old = subprocess.check_output(['git', '-C', str(root), 'show', 'HEAD:daemon/usb.cpp'], text=True)
assert 'usb_legacy_t110.h' not in old
new = old.replace('static void usb_ffs_open_thread() {', '#include "usb_legacy_t110.h"\n\nstatic void usb_ffs_open_thread() {')
before = '''        transport->SetConnection(std::make_unique<UsbFfsConnection>(
                std::move(control), std::move(bulk_out), std::move(bulk_in),
                std::move(destruction_notifier)));'''
after = '''        if (android::base::GetBoolProperty("ro.t110.legacy_usb", false)) {
            auto connection = std::make_unique<T110LegacyUsbConnection>(
                    std::move(control), std::move(bulk_out), std::move(bulk_in),
                    std::move(destruction_notifier));
            transport->SetConnection(std::make_unique<BlockingConnectionAdapter>(std::move(connection)));
        } else {
            transport->SetConnection(std::make_unique<UsbFfsConnection>(
                    std::move(control), std::move(bulk_out), std::move(bulk_in),
                    std::move(destruction_notifier)));
        }'''
assert new.count(before) == 1
new = new.replace(before, after)
header = (project / 'work/native-ramdisk/usb_legacy_t110.h').read_text()
patch = ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile='a/daemon/usb.cpp', tofile='b/daemon/usb.cpp'))
patch += ''.join(difflib.unified_diff([], header.splitlines(True), fromfile='/dev/null', tofile='b/daemon/usb_legacy_t110.h'))
out = project / 'patches/0013-adbd-t110-synchronous-functionfs.patch'
out.write_text(patch)
subprocess.run(['git', '-C', str(root), 'apply', '--cached', '--check', str(out)], check=True)
assert path.read_text() in [old, new], 'Unexpected edits to usb.cpp'
path.write_text(new)
(root / 'daemon/usb_legacy_t110.h').write_text(header)
print(out)
