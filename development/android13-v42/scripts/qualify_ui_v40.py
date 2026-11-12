"""Check ART acceptance and exercise real Settings/shade input on the installed boot."""
from pathlib import Path
import datetime,json,os,re,subprocess,sys,time
p=Path(__file__).resolve().parents[1]
boot46='--boot46' in sys.argv;live='--live-policy' in sys.argv;reclaim='--reclaim' in sys.argv or live
e=p/'evidence/ui-system-hang-20261112'/('v41-live-policy-ui' if live else ('v41-boot47-ui' if reclaim else ('v40-boot46-ui' if boot46 else 'v40-ui')));e.mkdir(exist_ok=True)
receipt=e/'result.json'
resume=None
if receipt.exists():
    resume=json.loads(receipt.read_text())
    assert not resume['actions'] and not resume.get('search_prebuilt_space_accepted'),'Do not repeat an interaction test'
    initial=(e/'dexopt.txt').read_text()
    assert 'DUMP TIMEOUT' in initial,'Only resume a documented initial read-only dump timeout'
    (e/'dexopt-initial-timeout.txt').write_text(initial)
installation=p/'evidence/ui-system-hang-20261112'/('v41-installation.json' if reclaim else ('boot46-installation.json' if boot46 else 'v40-installation.json'))
if '--wait-install' in sys.argv:
    deadline=time.monotonic()+900
    while time.monotonic()<deadline:
        install=json.loads(installation.read_text())
        if install['status']=='ANDROID_BOOT_COMPLETED_ART_ACCEPTANCE_AND_UI_RETEST_PENDING':break
        assert install['status'] in ['V40_IMAGE_VERIFIED_STARTING_ONE_FULL_BOOT','V41_IMAGE_VERIFIED_STARTING_ONE_FULL_BOOT','BOOT46_VERIFIED_STARTING_ONE_FULL_BOOT'],install['status']
        time.sleep(3)
    else:raise TimeoutError('Installation did not report Android boot completed')
install=json.loads(installation.read_text())
assert install['status']=='ANDROID_BOOT_COMPLETED_ART_ACCEPTANCE_AND_UI_RETEST_PENDING'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=45):
    r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
    return r.returncode,(r.stdout+r.stderr).decode(errors='replace').replace('\r','').strip()
def save_text(name,command,timeout=45):
    code,text=sh(command,timeout);(e/(name+'.txt')).write_text(text+'\n',encoding='utf-8');return code,text
assert sh('cat /sys/block/mmcblk0/device/cid')[1]=='1101003030384745T110_ADB_SERIAL'
boot=sh('cat /proc/sys/kernel/random/boot_id')[1];server=sh('pidof system_server')[1]
assert boot==install['boot_id'] and server==install['system_server']
record=dict(started=datetime.datetime.now().astimezone().isoformat(),boot_id=boot,system_server=server,actions=[],ui_fixed=False,physical_owner_confirmation=False)
if resume:
    assert resume['boot_id']==boot and resume['system_server']==server
    record.update(started=resume['started'],initial_package_dump_timed_out=True)
def save():receipt.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
save()
code,dexopt=save_text('dexopt','dumpsys -t 60 package dexopt',90)
section=re.search(r'\[com.google.android.googlequicksearchbox\](.*?)(?=\n\s*\[[a-zA-Z0-9_.]+\]|\Z)',dexopt,re.S)
assert code==0 and section and '[status=space]' in section[1] and '[reason=prebuilt]' in section[1],section[1] if section else 'No Search status'
record['search_prebuilt_space_accepted']=True;record['search_dexopt']=section[1].strip()
save_text('events-before','logcat -d -b events -v monotonic -t 4000')
_,last_before=save_text('last-anr-before','dumpsys activity lastanr')
ui_before=sh('pidof com.android.systemui')[1]
assert ui_before.isdigit()
save_text('memory-before','cat /proc/meminfo; cat /proc/vmstat')
commands=[('wake','input keyevent KEYCODE_WAKEUP; wm dismiss-keyguard'),
          ('open-settings','am start -W -a android.settings.SETTINGS')]
for cycle in range(3):
    commands += [(f'scroll-down-{cycle}','input swipe 300 800 300 300 400'),
                 (f'scroll-up-{cycle}','input swipe 300 300 300 800 400'),
                 (f'expand-shade-{cycle}','cmd statusbar expand-notifications'),
                 (f'collapse-shade-{cycle}','input swipe 300 850 300 180 450')]
commands += [('home','input keyevent KEYCODE_HOME'),('settings-again','am start -W -a android.settings.SETTINGS')]
for name,command in commands:
    started=time.monotonic()
    try:
        code,text=sh(command,45)
        record['actions'].append(dict(name=name,exit_code=code,seconds=round(time.monotonic()-started,3),output=text[-1500:]))
    except subprocess.TimeoutExpired:
        record['actions'].append(dict(name=name,timed_out=True));save();break
    save();time.sleep(2)
save_text('events-after','logcat -d -b events -v monotonic -t 4000')
_,last=save_text('last-anr-after','dumpsys activity lastanr')
save_text('logcat-after','logcat -d -b all -t 4000')
save_text('memory-after','cat /proc/meminfo; cat /proc/vmstat')
save_text('cpu-after','dumpsys cpuinfo')
save_text('focus-after','dumpsys window windows')
_,pids=save_text('search-code-maps',"pidof com.google.android.googlequicksearchbox; grep 'r-xp.*Velvet.odex' /proc/[0-9]*/maps")
save_text('processes','ps -A')
r=subprocess.run(adb+['exec-out','screencap','-p'],capture_output=True,timeout=60)
if r.returncode==0 and r.stdout.startswith(b'\x89PNG\r\n\x1a\n'):(e/'settings-after.png').write_bytes(r.stdout)
before_anrs={line for line in (e/'events-before.txt').read_text().splitlines() if 'am_anr' in line}
anr_lines=[line for line in (e/'events-after.txt').read_text().splitlines() if 'am_anr' in line and line not in before_anrs]
memory=(e/'memory-after.txt').read_text()
swap_out=re.search(r'^pswpout\s+(\d+)',memory,re.M)
swap_in=re.search(r'^pswpin\s+(\d+)',memory,re.M)
swap_total=re.search(r'^SwapTotal:\s+(\d+)',memory,re.M);swap_free=re.search(r'^SwapFree:\s+(\d+)',memory,re.M)
record.update(same_boot_and_server=sh('cat /proc/sys/kernel/random/boot_id')[1]==boot and sh('pidof system_server')[1]==server,
              new_anr_events_during_interaction=anr_lines,anr_events_already_in_baseline=sorted(before_anrs),no_last_anr='no anr has occurred since boot' in last.lower(),
              actions_completed=len(record['actions'])==len(commands),search_oat_mapped=bool(re.search(r'[0-9a-f]+-[0-9a-f]+ r-xp[^\n]*Velvet\.odex',pids)),
              swap_out_pages=int(swap_out[1]) if swap_out else None,swap_in_pages=int(swap_in[1]) if swap_in else None,
              swap_used_kib=int(swap_total[1])-int(swap_free[1]) if swap_total and swap_free else None)
record['same_systemui_process']=sh('pidof com.android.systemui')[1]==ui_before
before_identity='\n'.join(last_before.splitlines()[:4]);after_identity='\n'.join(last.splitlines()[:4])
record['last_anr_identity_unchanged']=before_identity==after_identity
clean=record['same_boot_and_server'] and record['same_systemui_process'] and not anr_lines and (record['last_anr_identity_unchanged'] if live else record['no_last_anr']) and record['actions_completed'] and all(item.get('exit_code')==0 for item in record['actions'])
if reclaim:clean=clean and bool(record['swap_out_pages'])
record['status']=('LIVE_INTERACTION_NO_NEW_ANR_EARLIER_BOOT_FAILED' if live else 'AUTOMATED_INTERACTION_NO_ANR_PHYSICAL_RESPONSIVENESS_UNVERIFIED') if clean else 'UI_QUALIFICATION_FAILED_OR_INCOMPLETE'
save();print(json.dumps({key:value for key,value in record.items() if key not in ['actions','search_dexopt']},indent=2))
