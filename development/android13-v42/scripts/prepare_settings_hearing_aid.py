from pathlib import Path
import difflib, subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
t=Path('/root/t110-build/lineage20/packages/apps/Settings')
name='src/com/android/settings/accessibility/AccessibilityHearingAidPreferenceController.java'
old=(t/name).read_text()
assert 'if (mLocalBluetoothManager == null) return;' not in old
new=old.replace('    public void onStart() {','    public void onStart() {\n        if (mLocalBluetoothManager == null) return;')
new=new.replace('    public void onStop() {','    public void onStop() {\n        if (mLocalBluetoothManager == null) return;')
new=new.replace('if (mBluetoothAdapter == null || !mBluetoothAdapter.isEnabled()) {',
                'if (mLocalBluetoothManager == null || mBluetoothAdapter == null\n                || !mBluetoothAdapter.isEnabled()) {')
patch=p/'patches/0070-settings-hearing-aid-without-bluetooth.patch'
assert not patch.exists()
patch.write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+name,tofile='b/'+name)))
subprocess.run(['git','apply','--check',str(patch)],cwd=t,check=True)
subprocess.run(['git','apply',str(patch)],cwd=t,check=True)
build=p/'scripts/build_system_image.sh'; s=build.read_text()
anchor="'packages/apps/Settings:0069-settings-t110-optional-usb-ethernet.patch'"
assert s.count(anchor)==1
build.write_text(s.replace(anchor,anchor+" 'packages/apps/Settings:0070-settings-hearing-aid-without-bluetooth.patch'"))
print('HEARING_AID_LIFECYCLE_GUARDS_APPLIED')
