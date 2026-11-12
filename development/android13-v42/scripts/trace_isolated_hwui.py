"""Trace only the temporary HWUI test app; restore all four GPU settings."""
from pathlib import Path
import argparse,datetime,json,os,re,shlex,subprocess
parser=argparse.ArgumentParser();parser.add_argument('--action',choices=('hwui','gles','hwui-suite'),default='hwui');parser.add_argument('--label',default='hwui-trace');parser.add_argument('--finish',action='store_true');parser.add_argument('--inspect',action='store_true');parser.add_argument('--skia-like',action='store_true');parser.add_argument('--width',type=int,default=64);parser.add_argument('--height',type=int,default=64);parser.add_argument('--extended',action='store_true');parser.add_argument('--no-layer',action='store_true');options=parser.parse_args()
assert re.fullmatch(r'[a-z0-9-]+',options.label)
p=Path(__file__).resolve().parents[1];out=p/'evidence/hardware-v35'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(command,timeout=20,check=True):
    r=subprocess.run(adb+['shell',command],capture_output=True,timeout=timeout)
    if check:assert r.returncode==0,r.stderr.decode(errors='replace')
    return r.stdout.decode(errors='replace').strip()
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
boot=sh('cat /proc/sys/kernel/random/boot_id');server=sh('pidof system_server')
settings={'enable_gpu_debug_layers':'1','gpu_debug_app':'dev.tapuz.t110.interaction',
          'gpu_debug_layers_gles':'libt110_gles_audit.so','gpu_debug_layer_app':'dev.tapuz.t110.interaction'}
original={key:sh('settings get global '+key) for key in settings}
if options.no_layer:assert all(v=='null' for v in original.values()),'Native-only verification requires no injected GLES layer'
record=dict(status='TRACE_STARTED',host_time=datetime.datetime.now().astimezone().isoformat(),
            boot_id=boot,system_server=server,original_settings=original,global_properties_changed=False,layer_injection_requested=not options.no_layer)
path=out/(options.label+'.json')
def save():path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
assert not path.exists(),'Review the prior trace before running another'
save()
try:
    if not options.no_layer:
        for key,value in settings.items():sh('settings put global '+key+' '+shlex.quote(value))
    text=sh('am instrument --no-hidden-api-checks -w -e action '+options.action+' -e width '+str(options.width)+' -e height '+str(options.height)+(' -e extended true' if options.extended else '')+(' -e finish true' if options.finish else '')+(' -e inspect true' if options.inspect else '')+(' -e skiaLike true' if options.skia_like else '')+' dev.tapuz.t110.interaction/.InteractionInstrumentation',150,False)
    (out/(options.label+'-result.txt')).write_text(text+'\n',encoding='utf-8')
    match=re.search(r'INSTRUMENTATION_RESULT: report=(.*)',text)
    record['render_result']=json.loads(match[1]) if match else {'error':'No instrumentation report'}
    logs=sh("logcat -d -t 2000 -s T110GlesAudit:I '*:S'",30)
    pid=record['render_result'].get('pid')
    if pid:logs='\n'.join(line for line in logs.splitlines() if re.search(r'\s'+str(pid)+r'\s+\d+\s+I T110GlesAudit:',line))
    (out/(options.label+'-gles.txt')).write_text(logs+'\n',encoding='utf-8')
    record['layer_loaded']='initialized scoped GLES trace' in logs
finally:
    restored={}
    for key,value in original.items():
        sh('settings delete global '+key if value=='null' else 'settings put global '+key+' '+shlex.quote(value))
        restored[key]=sh('settings get global '+key)==value
    record['settings_restored']=restored
    record['boot_and_server_stable']=sh('cat /proc/sys/kernel/random/boot_id')==boot and sh('pidof system_server')==server
    record['status']='TRACE_CAPTURED_SETTINGS_RESTORED' if all(restored.values()) else 'RESTORATION_FAILED'
    save()
print(json.dumps(record,indent=2))
