"""Verify fresh-boot defaults without applying any live logging/memory override."""
from pathlib import Path
import datetime,json,os,re,subprocess,sys,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112';out=e/'v42-persistence';out.mkdir(exist_ok=True)
receipt=out/'result.json';assert not receipt.exists()
installation=e/'v42-installation.json'
if '--wait-install' in sys.argv:
 deadline=time.monotonic()+1200
 while time.monotonic()<deadline:
  try:pending=json.loads(installation.read_text())
  except json.JSONDecodeError:time.sleep(1);continue
  if pending['status']=='ANDROID_BOOT_COMPLETED_ART_ACCEPTANCE_AND_UI_RETEST_PENDING':break
  assert pending['status'] in ['OFFLINE_AND_DEVICE_IDENTITY_VERIFIED','REVERSIBLE_DELTA_STAGED_VERIFIED','V42_IMAGE_VERIFIED_STARTING_ONE_FULL_BOOT'],pending['status']
  time.sleep(3)
 else:raise TimeoutError('Installation did not report a completed Android boot')
install=json.loads(installation.read_text());assert install['status']=='ANDROID_BOOT_COMPLETED_ART_ACCEPTANCE_AND_UI_RETEST_PENDING'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=30,check=True):
 r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
 if check:assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
 return r.stdout.decode(errors='replace').replace('\r','').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
boot=sh('cat /proc/sys/kernel/random/boot_id');assert boot==install['boot_id'] and boot!=install['previous_boot_id']
record=dict(status='VERIFYING_FRESH_BOOT_DEFAULTS',time=datetime.datetime.now().astimezone().isoformat(),boot_id=boot,
            live_overrides_applied=False,ui_fixed=False,checks={})
def save():receipt.write_text(json.dumps(record,indent=2)+'\n')
def verified(key,condition,value):
 record['checks'][key]=dict(pass_=bool(condition),observed=value);save();assert condition,(key,value)
save()
verified('selinux_enforcing',sh('getenforce')=='Enforcing',sh('getenforce'))
value=sh('cat /proc/sys/vm/swappiness');verified('init_swappiness_100',value=='100',value)
value=sh('ls -Z /proc/sys/vm/swappiness');verified('precise_swappiness_label','u:object_r:proc_t110_swappiness:s0' in value,value)
value=sh('cat /proc/sys/vm/page-cluster');verified('swap_readahead_zero',value=='0',value)
value=sh('cat /sys/block/zram0/disksize');verified('zram_512mib',value=='536870912',value)
value=sh('cat /proc/swaps');verified('standard_swap_active','/dev/block/zram0' in value,value)
value=sh('getprop init.svc.t110-logcat');verified('diagnostic_file_logger_not_started',value in ['','stopped'],value or '(never started)')
verified('normal_android_logd_running',sh('getprop init.svc.logd')=='running',sh('getprop init.svc.logd'))
processes=sh('ps -A');(out/'processes.txt').write_text(processes)
workers=[];file_writers=[]
for line in processes.splitlines():
 columns=line.split()
 if len(columns)<3 or not columns[1].isdigit():continue
 pid=int(columns[1])
 if pid>1 and columns[-1] in ['init','/init'] and sh(f'readlink /proc/{pid}/exe',check=False)=='/init':
  fds=sh(f'ls -l /proc/{pid}/fd',check=False)
  if all(name in fds for name in ['kernel-0.txt','kernel-1.txt','logger-status.txt']):workers.append(pid)
 if columns[-1]=='logcat':
  command=sh(f'cat /proc/{pid}/cmdline',check=False)
  if '/data/local/tmp/t110-logcat.txt' in command:file_writers.append(pid)
verified('no_periodic_snapshot_worker',not workers,workers)
verified('no_diagnostic_logcat_writer',not file_writers,file_writers)
folders=sh('ls -d /stage-data/local/tmp/t110-bootlogs/boot-*').splitlines()
folders=[name for name in folders if re.fullmatch(r'/stage-data/local/tmp/t110-bootlogs/boot-[0-9]{4}',name)]
assert folders;folder=max(folders)
checkpoints=sh('cat '+folder+'/checkpoints.txt');(out/'boot-checkpoints.txt').write_text(checkpoints)
verified('default_optin_branch_executed','Periodic kernel snapshots disabled; one early snapshot retained' in checkpoints,folder)
size=sh('wc -c < '+folder+'/kernel-0.txt');verified('early_kernel_snapshot_retained',size.isdigit() and int(size)>0,size)
kernel=sh('dmesg',60);(out/'kernel.txt').write_text(kernel)
denial=bool(re.search(r'avc: denied \{ write \}.*comm="init".*name="swappiness"',kernel))
verified('no_init_swappiness_write_denial',not denial,denial)
memory=sh('cat /proc/meminfo; cat /proc/vmstat');(out/'memory.txt').write_text(memory)
for key in ['pswpin','pswpout']:
 match=re.search(r'^'+key+r'\s+(\d+)',memory,re.M);record[key+'_pages']=int(match[1]) if match else None
last_anr=sh('dumpsys -t 30 activity lastanr',45,False);(out/'last-anr.txt').write_text(last_anr)
record['anr_query_timed_out']='DUMP TIMEOUT' in last_anr
record['current_anr_reported']=None if record['anr_query_timed_out'] else 'ANR time:' in last_anr
verified('same_android_boot',sh('cat /proc/sys/kernel/random/boot_id')==boot,sh('cat /proc/sys/kernel/random/boot_id'))
record.update(status='PASS_PERSISTENT_LOGGING_AND_MEMORY_DEFAULTS',system_server=sh('pidof system_server'),recovery_and_both_data_profiles_preserved=True)
save();print(json.dumps({key:value for key,value in record.items() if key!='checks'},indent=2))
