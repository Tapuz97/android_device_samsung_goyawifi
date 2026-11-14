"""Record the owner's return to14.1 without altering either ROM source tree."""
from pathlib import Path
import json,shutil
from recovery_transport import BASE,adb
dest=BASE/'tests/lineage14-restored-20261114'
restore=json.loads((dest/'restore-verification.json').read_text(encoding='utf-8'))
boot=json.loads((dest/'restored-boot-verification.json').read_text(encoding='utf-8'))
assert boot['status']=='PASS_RESTORED14_BOOT_COMPLETED'
assert adb('shell','getprop ro.build.version.sdk').strip()=='25'
assert adb('shell','settings get secure camera_double_tap_power_gesture_disabled').strip()=='1'
record=dict(status='WORKING14_RESTORED_OWNER_CONFIRMED',boot_id=boot['boot_id'],
    system_sha256=restore['system_sha256'],boot_sha256=restore['boot_sha256'],
    recovery_unchanged=True,physical_system_written=False,original14_data_preserved=True,
    owner_confirmed_home_and_touch=True,camera_double_tap_power_gesture_disabled=1,
    owner_confirmed_single_power_press_sleeps=True,android13_work_preserved=True,
    active_direction='Lineage14.1 native UI improvements; Android13 port stopped by owner',
    ui_redesign_installed=False,boot_animation_crash_observed=True)
def write(path,text):path.write_text(text,encoding='utf-8',newline='\n')
write(dest/'restore-result.json',json.dumps(record,indent=2)+'\n')
audit=Path(r'\\wsl.localhost\Ubuntu\root\t110-android13-audit\device')
public=audit/'development/lineage14-return-20261114';public.mkdir(exist_ok=True)
for filename in ('RESTORED-LINEAGE14-20261114.md','LINEAGE14-UI-DIRECTION.md'):
    shutil.copy2(BASE/filename,public/filename)
for filename in ('restore-result.json','restore-verification.json','restored-boot-verification.json'):
    write(public/filename,json.dumps(json.loads((dest/filename).read_text(encoding='utf-8')),indent=2)+'\n')
(public/'tools').mkdir(exist_ok=True)
for filename in ('restore_working_lineage14.py','verify_restored_lineage14_boot.py','record_lineage14_restore.py','recovery_transport.py'):
    text=(BASE/'scripts'/filename).read_text(encoding='utf-8')
    write(public/'tools'/filename,'\n'.join(line.rstrip() for line in text.splitlines())+'\n')
write(public/'TOOLS-NOTES.md','''# Owner-specific restoration tools

Original location: SM-T110/scripts. The archive is a record, not an end-user
installer. Paths, exact hashes and device identity guards refer to the owner's
verified C:/Ubuntu environment. Android13 archives and both14.1 pairs remain
preserved. Restoration required the14.1 system file as well as KERNEL, while
retaining its original data. Keep these tools in scripts when restoring their
original workspace; recovery_transport derives BASE from its parent directory.
''')
status=BASE/'CURRENT-STATUS.md';old=status.read_text(encoding='utf-8');history=old[old.index('\n---\n'):]
write(status,'''# Active: working LineageOS14.1 restored; native UI improvements next

Owner stopped Android13 compatibility work on2026-11-14. The previous14.1 media
build is restored, fully readback-verified and booted with the original data.
Owner confirmed Home/touch work. Single Power press now sleeps after disabling
the camera double-press shortcut in secure settings; the owner confirmed this.

System01165196, boot93aa73c2; recovery unchanged; physical SYSTEM never written.
Boot ID77b5b670-acf7-41dd-a498-a49d9972b8af.14.1 images/source and13 source/images
remain backed up. See [restore results](RESTORED-LINEAGE14-20261114.md) and
[UI direction](LINEAGE14-UI-DIRECTION.md). No UI redesign has been installed yet.
The restore crash buffer had a BootAnimation SIGSEGV; do not claim all startup
processes are error-free. Home and Settings ran; physical Home/touch were confirmed.
'''+history)
main=BASE/'README.md';body=main.read_text(encoding='utf-8')
marker='Latest direction: '
if marker not in body:
    body=body.replace('\n\n','\n\nLatest direction: [working14.1 restored](RESTORED-LINEAGE14-20261114.md); [native UI improvements](LINEAGE14-UI-DIRECTION.md). Android13 work is preserved and stopped at the owner\'s request.\n\n',1)
body=body.replace('Current investigation: [Android13 offline audit and fixes](android13-audit/README.md).',
                  'Archived investigation: [Android13 audit and test results](android13-audit/README.md).')
body=body.replace('Android10 is deferred while\nwe apply the hardware lessons to the prior Android13 source; no flash is authorized\nuntil the combined fixes are ready.',
                  'Android10 and Android13 platform work are deferred. Active development returns\nto the working14.1 base and its native UI.')
body=body.replace('the last14.1 qualification is preserved; Android13 is now installed for development.',
                  '14.1 has been restored after the archived Android13 experiment.')
write(main,body)
header='# Current direction: restored working14.1, then native UI improvements\n\n'
root=audit/'development/android13-audit-20261114/README.md';body=root.read_text(encoding='utf-8')
if not body.startswith(header):
    write(root,header+'Owner ended the13 port and requested the working14.1 base. Restoration and\n'
          'physical Home/touch/Power checks passed. Original14.1 data is retained;13 work\n'
          'stays backed up. See [restore results](../lineage14-return-20261114/RESTORED-LINEAGE14-20261114.md)\n'
          'and [UI direction](../lineage14-return-20261114/LINEAGE14-UI-DIRECTION.md).\n\n---\n\n'+body)
root=BASE/'android13-audit/README.md';body=root.read_text(encoding='utf-8')
if not body.startswith(header):
    write(root,header+'The13 experiment is archived. See [restore results](../RESTORED-LINEAGE14-20261114.md)\n'
          'and [UI direction](../LINEAGE14-UI-DIRECTION.md). Historical13 results follow.\n\n---\n\n'+body)
print('Recorded restored14.1, confirmed Power behavior and the owner\'s UI direction. ROM sources unchanged.')
