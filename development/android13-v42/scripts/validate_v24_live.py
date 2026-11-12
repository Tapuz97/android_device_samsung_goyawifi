"""Check app navigation and two screen sleep/wake cycles on the installed boot."""
from pathlib import Path
import argparse, json, os, re, subprocess, time
p = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('trial',type=Path)
args=parser.parse_args(); trial=args.trial
assert trial.is_dir()
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def shell(cmd,timeout=20):
    r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=timeout)
    assert r.returncode==0,(cmd,r.stdout,r.stderr)
    return r.stdout.decode(errors='replace')
assert shell('cat /sys/block/mmcblk0/device/cid').strip()=='1101003030384745T110_ADB_SERIAL'
assert shell('getprop sys.boot_completed').strip()=='1'
assert shell('getprop ro.product.device').strip()=='t110_bringup'
pair=json.loads((p/'artifacts/lineage20-rom-v24/rom-pair.json').read_text())
assert shell('md5sum /dev/block/mmcblk0p10').split()[0]==pair['boot_md5']
assert shell('pm path com.android.launcher3').strip()=='package:/system/system_ext/priv-app/TrebuchetQuickStep/TrebuchetQuickStep.apk'
shell('input keyevent 224')
time.sleep(3)
start=float(shell('cat /proc/uptime').split()[0])
before=shell('cat /proc/sys/kernel/random/boot_id; pidof system_server; pidof com.android.systemui; pidof com.android.launcher3').splitlines()
assert len(before)==4
results={'start_uptime':start,'processes_before':before,'cycles':[],'additional_boots':0,'physical_confirmation':'PENDING'}
def logs():
    return shell('logcat -b main -d -s T110V24Validation:I SurfaceFlinger:D T110Framebuffer:I')
try:
    for cycle in (1,2):
        marker=f'cycle{cycle}_off'
        shell('log -t T110V24Validation '+marker)
        shell('input keyevent 223')
        time.sleep(2)
        tail=logs().split(marker)[-1]
        assert 'Finished setting power mode 0' in tail,tail[-1200:]
        marker=f'cycle{cycle}_on'
        shell('log -t T110V24Validation '+marker)
        t=time.monotonic(); shell('input keyevent 224')
        while time.monotonic()-t<8:
            tail=logs().split(marker)[-1]
            if 'Finished setting power mode 2' in tail:break
            time.sleep(.4)
        else:raise AssertionError('Display wake exceeded8sec: '+tail[-1200:])
        results['cycles'].append(dict(cycle=cycle,wake_observed_seconds=round(time.monotonic()-t,3)))
        time.sleep(2)
    shell('wm dismiss-keyguard; cmd statusbar collapse')
    time.sleep(2)
    for label,command in [
        ('home','input keyevent 3'),
        ('drawer','input swipe 300 900 300 250 500'),
        ('settings','am start -W -a android.settings.SETTINGS'),
        ('settings-scroll','input swipe 300 840 300 300 500'),
        ('recents','input keyevent 187'),
    ]:
        output=shell(command,timeout=40)
        (trial/f'v24-{label}-action.txt').write_text(output,encoding='utf-8')
        time.sleep(3)
        subprocess.run(['python',str(p/'scripts/capture_v26_framebuffer.py'),str(trial),'--label','v24-'+label],check=True,timeout=40)
    shell('input keyevent 3')
    results['processes_after']=shell('cat /proc/sys/kernel/random/boot_id; pidof system_server; pidof com.android.systemui; pidof com.android.launcher3').splitlines()
    assert before==results['processes_after'],'Core process restarted during interaction checks'
    kernel=shell('dmesg')
    (trial/'v24-interaction-kernel.txt').write_text(kernel,encoding='utf-8')
    recent=[]
    for line in kernel.splitlines():
        m=re.match(r'\[\s*([\d.]+)\]',line)
        if m and float(m.group(1))>=start and re.search(r'slave_0x(?:20|64).*error:',line):recent.append(line)
    assert not recent,recent
    results['new_touch_or_bridge_i2c_errors']=recent
    results['status']='SAME_BOOT_INTERACTION_CHECKS_COMPLETED_VISUAL_REVIEW_REQUIRED'
finally:
    (trial/'v24-power-transitions.txt').write_text(logs(),encoding='utf-8')
    (trial/'v24-live-checks.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,indent=2))
