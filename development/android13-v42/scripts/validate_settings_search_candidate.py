"""Exercise all search indexing endpoints on the installed Settings update."""
from pathlib import Path
import json, os, re, shlex, subprocess, time
p = Path(__file__).resolve().parents[1]
e = p / 'evidence/offline-v36/settings-candidate'
adb = [str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'), '-s', 'T110_ADB_SERIAL']
def sh(command, timeout=120):
    r = subprocess.run(adb+['shell', command], capture_output=True, timeout=timeout)
    assert r.returncode == 0, (command, r.stdout.decode(errors='replace'), r.stderr.decode(errors='replace'))
    return r.stdout.decode(errors='replace').strip()
install = json.loads((e/'installation.json').read_text())
assert sh('sha256sum ' + install['installed_path']).split()[0] == install['sha256']
report = dict(status='RUNNING', additional_boots=0, queries=[])
probe = p/'evidence/offline-v36/clip-probe/probe.jar'
assert probe.is_file()
subprocess.run(adb+['push',str(probe),'/data/local/tmp/t110-clip-probe.jar'],capture_output=True,check=True,timeout=30)
zygote = sh('pidof zygote').split()[0]
assert zygote.isdigit()
environment = subprocess.check_output(adb+['exec-out','cat /proc/'+zygote+'/environ'],timeout=30).decode()
allowed = {'BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','ANDROID_ART_ROOT','ANDROID_I18N_ROOT','ANDROID_TZDATA_ROOT'}
env = dict(entry.split('=',1) for entry in environment.split('\0') if '=' in entry and entry.split('=',1)[0] in allowed)
assert env.get('BOOTCLASSPATH')
prefix = ' '.join(k+'='+shlex.quote(v) for k,v in env.items())
query_command = prefix+' CLASSPATH=/data/local/tmp/t110-clip-probe.jar:/system/framework/content.jar timeout 150 app_process /system/bin T110ClipProbe query --uri '
try:
    report['before_exit_info'] = sh('dumpsys activity exit-info com.android.settings')
    report['start_device_time'] = sh('date +%s')
    for endpoint in ['indexables_xml_res', 'non_indexables_key', 'indexables_raw', 'dynamic_indexables_raw', 'site_map_pairs']:
        start = time.monotonic()
        output = sh(query_command+'content://com.android.settings/settings/' + endpoint, 180)
        (e/(endpoint+'.txt')).write_text(output, encoding='utf-8')
        assert 'Row: ' in output or 'No result found.' in output, output[-2000:]
        assert 'Error while accessing provider' not in output and 'DeadObjectException' not in output, output[-2000:]
        pid = sh('pidof com.android.settings')
        assert pid.isdigit(), pid
        report['queries'].append(dict(endpoint=endpoint, rows=output.count('Row: '),
                                      seconds=round(time.monotonic()-start,2), pid=pid))
        print(endpoint, report['queries'][-1], flush=True)
    assert len({item['pid'] for item in report['queries']}) == 1, report
    report['after_exit_info'] = sh('dumpsys activity exit-info com.android.settings')
    exits = lambda value: re.findall(r'timestamp=.*?pid=.*',value)
    assert exits(report['after_exit_info']) == exits(report['before_exit_info'])
    assert sh('cat /proc/sys/kernel/random/boot_id; pidof system_server').splitlines() == install['boot_and_server']
    report['status'] = 'INDEXING_ENDPOINTS_PASS_UI_PENDING'
finally:
    (e/'runtime-indexing.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
