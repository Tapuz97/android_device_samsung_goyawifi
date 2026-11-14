from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile
BASE=Path(__file__).resolve().parents[1];TOOLS=BASE/'android13-audit'
LOCAL=BASE/'tests/android13-complete-20261114'
AUDIT=Path(r'\\wsl.localhost\Ubuntu\root\t110-android13-audit')
WORK=AUDIT/'hardware-test-20261114'
REPO=AUDIT/'device';PUBLIC=REPO/'development/android13-audit-20261114/hardware-test-1'
PUBLIC.mkdir(exist_ok=True)
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def write(path,text):path.write_text(text,encoding='utf-8',newline='\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
install=read(LOCAL/'install-verification.json');boot=read(LOCAL/'boot-timeline.json')
assert install['status']=='ANDROID13_CANDIDATE_INSTALLED_READBACK_VERIFIED_NOT_BOOTED'
assert boot['status']=='ANDROID13_REPORTS_BOOT_COMPLETED'
events=(LOCAL/'touch-events.txt').read_text(encoding='utf-8')
contacts=sum('ABS_MT_TRACKING_ID' in line and 'ffffffff' not in line for line in events.splitlines())
assert contacts>0
gap=read(WORK/'audio-routing-gap.json');assert len(gap['modules'])==6
assert all(not row['present_in_android13'] for row in gap['modules'])
result=dict(status='HARDWARE_QUALIFICATION_FAILED_FUNCTIONAL_GAPS_REMAIN',full_candidate_boots=1,
    boot_id=boot['boot_id'],android_sdk=33,boot_completed_observed=True,
    host_monitor_first_completion_seconds=boot['elapsed'],user_setup_complete=True,
    display=dict(status='PARTIAL',owner_saw_animation=True,owner_completed_setup=True,
                 top_left_artifacts_owner_and_screenshot=True),
    touch=dict(status='PASS_TESTED_FLOW',owner_confirmed_start_and_setup=True,recorded_contacts=contacts),
    speaker=dict(status='FAIL_PLAYBACK_INITIALIZATION',audible_playback_confirmed=False,
                 media_player_error=-19,primary_output_available=False,missing_dynamic_audio_path_modules=6),
    startup=dict(status='FAIL_ANRS_BEFORE_RECOVERY',system_and_systemui_anrs=True),
    bluetooth=dict(status='FAIL_OBSERVED_HAL_CONTROLLER_TIMEOUT'),
    system_sha256=install['system_sha256'],boot_sha256=install['boot_sha256'],
    recovery_sha256=install['recovery_sha256'],recovery_unchanged=True,physical_system_written=False,
    working14_host_pair_preserved=True,working14_on_tablet_data_preserved=True,
    working14_on_tablet_system_file_reclaimed_after_host_and_tablet_hash_comparison=True,
    working14_online_release_id=444868203,android13_candidate_online_release_id=445434326,
    same_boot_audio_service_reinitializations=1,system_image_modified_during_runtime=False,
    usb_stay_awake_original_and_restored=0,continuous_device_logging_enabled=False,
    private_userdata_archive_uploaded=False,
    screenshot=dict(file='setup-complete-screen.png',sha256=sha(LOCAL/'setup-complete-screen.png')))
for dest in (LOCAL,WORK,PUBLIC):write(dest/'hardware-test-verification.json',json.dumps(result,indent=2)+'\n')
shutil.copy2(TOOLS/'HARDWARE-TEST-1.md',PUBLIC/'RESULTS.md')
shutil.copy2(TOOLS/'HARDWARE-TOOLS-NOTES.md',PUBLIC/'TOOLS-NOTES.md')
(PUBLIC/'prerequisites').mkdir(exist_ok=True)
shutil.copy2(BASE/'scripts/recovery_transport.py',PUBLIC/'prerequisites/recovery_transport.py')
shutil.copy2(WORK/'audio-routing-gap.json',PUBLIC/'audio-routing-gap.json')
names=('backup_tablet_test_data.py','install_complete_candidate.py','monitor_one_boot.py',
       'capture_boot_snapshot.py','record_touch_once.py','capture_audio_initialization.py',
       'save_hardware_test1_record.py')
(PUBLIC/'tools').mkdir(exist_ok=True)
for name in names:shutil.copy2(TOOLS/name,PUBLIC/'tools'/name)
with zipfile.ZipFile(WORK/'test1-private-evidence.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(LOCAL.rglob('*')):
        if path.is_file():archive.write(path,str(path.relative_to(LOCAL)))
with zipfile.ZipFile(WORK/'test1-private-evidence.zip') as archive:assert archive.testzip() is None
marker='# Latest hardware result: Android13 booted with functional defects\n'
root=REPO/'development/android13-audit-20261114/README.md'
body=root.read_text(encoding='utf-8')
if not body.startswith(marker):
    write(root,marker+'\nSee [hardware-test-1/RESULTS.md](hardware-test-1/RESULTS.md). One full candidate\nboot reached setup and the launcher. Owner-confirmed touch/setup work, but startup\nANRs, top-left rendering artifacts and missing audio routing modules remain.\nThe candidate is not hardware-qualified.14.1 images/source and isolated tablet\ndata are preserved; its tablet system file was reclaimed only after matching\nthe verified C: copy. Raw logs/userdata remain private and local.\n\n---\n\n'+body)
audit_readme=TOOLS/'README.md';body=audit_readme.read_text(encoding='utf-8')
if not body.startswith(marker):
    write(audit_readme,marker+'\nSee [HARDWARE-TEST-1.md](HARDWARE-TEST-1.md) for the actual single-boot result.\nSetup and touch work. Startup ANRs, top-left rendering artifacts and missing\naudio-routing modules prevent full qualification. Android13 is installed;14.1\nis preserved for rollback. The earlier offline results below remain historical\nchecks of the candidate, not a declaration of full hardware functionality.\n\n---\n\n'+body)
status=BASE/'CURRENT-STATUS.md';body=status.read_text(encoding='utf-8');historical=body[body.index('\n---\n'):]
write(status,'# Installed: Android13 test candidate — functional qualification incomplete\n\n'
    'One full boot test completed on2026-11-14. User completed setup and confirmed\n'
    'Start/touch work. Startup System/UI ANRs, top-left artifacts and failed speaker\n'
    'initialization remain. See [actual test results](android13-audit/HARDWARE-TEST-1.md).\n\n'
    'System47096189, bootf2d735c3; recovery unchanged; physical SYSTEM never written.\n'
    'Working14.1 images/source remain on C: and online. Its tablet data is preserved;\n'
    'restoring14.1 requires its backed-up system file as well as KERNEL. Old13 data\n'
    'was privately archived on C: before a fresh-data test. No second candidate boot\n'
    'was run. USB stay-awake0 restored and bounded diagnostic captures stopped.\n'
    +historical)
main=BASE/'README.md';body=main.read_text(encoding='utf-8')
body=body.replace('# SM-T110 LineageOS 14.1 development','# SM-T110 LineageOS development',1)
body=body.replace('Working14.1 remains the preserved installed baseline.','Working14.1 remains the preserved rollback baseline.',1)
body=body.replace('the tablet now runs Lineage14.1.','the last14.1 qualification is preserved; Android13 is now installed for development.',1)
if 'Latest hardware result:' not in body:
    body=body.replace('\n\n','\n\nLatest hardware result: [Android13 boots; setup/touch work; rendering/startup/audio defects remain](android13-audit/HARDWARE-TEST-1.md).\n\n',1)
write(main,body)
print(json.dumps(result,indent=2))
print('Saved public conclusions/tools and private local evidence. No further tablet action.')
