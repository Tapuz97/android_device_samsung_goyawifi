"""Capture the installed hardware checkpoint and update the operator records."""
from pathlib import Path
import collections,datetime,hashlib,json,os,re,subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def call(args,timeout=30):return subprocess.run(adb+list(map(str,args)),capture_output=True,timeout=timeout)
def sh(command,timeout=30):
    r=call(['shell',command],timeout);assert r.returncode==0,r.stderr.decode(errors='replace')
    return r.stdout.decode(errors='replace').strip()
installation=json.loads((e/'boot39-installation.json').read_text())
assert installation['status']=='ANDROID_BOOT_COMPLETED_QUALIFICATION_PENDING'
assert sh('cat /sys/block/mmcblk0/device/cid')=='1101003030384745T110_ADB_SERIAL'
assert sh('sha256sum /dev/block/mmcblk0p10').split()[0]==installation['boot_sha256']
record={'host_time':datetime.datetime.now().astimezone().isoformat(),'installed_system':'v34-GApps',
 'installed_boot':'BOOT39','boot_sha256':installation['boot_sha256'],
 'boot_id':sh('cat /proc/sys/kernel/random/boot_id'),'system_server':sh('pidof system_server'),
 'boot_completed':sh('getprop sys.boot_completed'),'getenforce':sh('getenforce'),
 'kernel':sh('uname -a'),'additional_boots_at_close':0,
 'packet_target_fix':'STAGED_NOT_BUILT_OR_INSTALLED','full_app_graphics':'FAIL'}
network=call(['shell','am instrument --no-hidden-api-checks -w -e action https dev.tapuz.t110.interaction/.InteractionInstrumentation'],45)
text=network.stdout.decode(errors='replace');(e/'final-app-network.txt').write_text(text,encoding='utf-8')
match=re.search(r'INSTRUMENTATION_RESULT: report=(.*)',text)
record['ordinary_app_network']=json.loads(match[1]) if match else {'error':'No instrumentation report','raw':'final-app-network.txt'}
(e/'final-wifi.txt').write_text(sh('cmd wifi status; ip rule; ip route show table all')+'\n',encoding='utf-8')
record['gpu_settings']={key:sh('settings get global '+key) for key in ('enable_gpu_debug_layers','gpu_debug_app','gpu_debug_layers_gles','gpu_debug_layer_app')}
assert all(value=='null' for value in record['gpu_settings'].values()),'Restore scoped test settings before closing'
record['stay_on']=sh('settings get global stay_on_while_plugged_in');assert record['stay_on']=='0'
record['advanced_restart']=sh('settings get --lineage secure advanced_reboot')
r=call(['uninstall','dev.tapuz.t110.interaction'],45)
record['temporary_test_app_removed']=r.returncode==0 and 'Success' in r.stdout.decode(errors='replace')
assert record['temporary_test_app_removed']
target='/data/local/tmp/t110-uid-routing-boot39.img'
if sh('test -f '+target+' && test ! -L '+target+' && echo FILE')=='FILE':
    assert sh('readlink -f '+target)==target
    assert sh('sha256sum '+target).split()[0]==installation['boot_sha256']
    assert hashlib.sha256((p/'artifacts/android13-boot-v39/KERNEL.img').read_bytes()).hexdigest()==installation['boot_sha256']
    sh('rm '+target)
    record['owned_boot_transfer_file_removed']=True
assert record['boot_id']==sh('cat /proc/sys/kernel/random/boot_id')
(e/'final-status.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')

status='''# Current state - v34-GApps / BOOT39, hardware work first

BOOT39 is installed and verified. SHA256
33462a6a2cffc1695ac8d8f986d42eac13b12b0708a5eb9db26f66c9baa73701.
It contains the UID-routing kernel; BOOT38 ramdisk is byte-identical. The v34
system remains SHA2569aaae33e0f8d52c65e46212842cfba82409a01cfe980356a11c668d4526a7151.
No system image rewrite/repack, physicalSYSTEM write, recovery write or data wipe.
Current boot a1d15767-b169-4593-818b-63132704d969, system_server311, SELinux Enforcing.
Startup completed in227.89s. UI lag/startup ANRs remain unresolved.

Patch0095 implements modern per-owner routing on Linux3.4: FRA_UID_RANGE20,
RTA_UID25, IPv4/IPv6 flow ownership, socket ownership and UID-aware IPv4 cache.
All71 isolated real-kernel QEMU regressions pass; compiled tablet kernel/modules
pass. Existing actual radio/graphics module loadable sections and normalized
relocations match the new build, allowing the tested boot-only update.
Evidence: evidence/hardware-v35/uid-qemu-result.json and module-equivalence.json.

The old runtime/source discrepancy is resolved: rtnetlink_rcv_msg's outer
attribute loop rejected type20 before nla_parse could ignore it. On BOOT39 the
real Android UID rules now appear. Native Wi-Fi authenticates and retains DHCP,
but networkAddInterface fails next with RemoteIO121 and routes fail ENODEV19.
MARK/CONNMARK/IDLETIMER targets are disabled in the running config. Patch0096,
netd-targets.config and build_netd_targets_kernel.sh are STAGED, NOT BUILT.
Normal-app Internet remains FAIL. Do not manually bypass per-app routing rules.

Direct GLES2 shader geometry passes all3 buffer modes, including CPU-queued
ImageReader pixels. A second3-case run with Skia's fragment shader, blend state,
32768-byte VBO and double orphan/subdata also passes. HWUI still returns4096 red,
0 green despite successful compile/link and correct uniforms/attribute locations.
Blend state is ONE/ONE_MINUS_SRC_ALPHA, FUNC_ADD. A post-swap commit callback with
glFinish and readback still reads red; it does not rule out pre-presentation sync
or ordering. No production HWUI policy was changed. SurfaceFlinger already uses
Vivante GLES2; app windows retain the existing software fallback.

Next native trace source captures actual uploaded vertex data and pre-swap GPU
pixels. That C source is NOT COMPILED: the retained .so/APK are older diagnostics.
build_gles_audit.sh now records source/library hashes, and the APK builder refuses
a stale trace layer. Rebuild native first. See hardware-v35/RESUME-ACTIVE.md.

Bluetooth: all3 SDIO functions exist, but mbt8xxx is not loaded and no Bluetooth
Manager/HAL/HCI device exists yet. Button keys remain mapped; illumination FAIL.
sec_touchkey exists but has no brightness/LED control. Board source mentions a
touchkey regulator in an optional RT5033 block, absent from the current regulator
inventory. Do not toggle guessed rails; owner confirmed LEDs work on stock.
Camera raw640x480 USERPTR capture is earlier PASS; Android provider is unfinished.
Audio/sensors remain separate incomplete hardware ports. Preserve native Lineage
and Google features, then address software after hardware functionality.

The external build SSD logged fresh Disk153 retries; Linux reads and startup
stalled. wsl--shutdown completed successfully; a subsequent Ubuntu-only startup
read still hangs. No build is running. User reconnect request is pending.
Ubuntu is on C (machineid3fa9d65f37d2414bb2f2b18f86ca1736); T110Build is on E
(machineidcd27023803954a89ad7c30407399c847). Device names sdd/sde can change.
Use cmd.exe/loginfalse for host tooling while PowerShell is stalled. Only exact
task-owned obsolete wrappers were cancelled; no user services were reset.

Tablet remains in Android; temporary test APK and this turn's verified BOOT
transfer file were removed. All4 GPU debug settings restored to absent, stay-on0,
Advanced Restart1. See evidence/hardware-v35/final-status.json.

Never write physicalSYSTEM/mmcblk0p15. Active system is the immutable userdata
loop file; both Android profiles remain. BOOT38 is the current rollback and
recovery SHAf7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e
is unchanged. Do not rerun install_uid_boot39.py. Old v32 deletion denials were
not retried. No Google binaries, private evidence or credentials were published.
'''
(p/'CURRENT-STATUS.md').write_text(status,encoding='utf-8')
resume='''# Resume hardware work - v34 system / BOOT39 installed

Read CURRENT-STATUS.md, FUNCTIONAL-CHECKLIST.md and evidence/hardware-v35/RESUME-ACTIVE.md.
The owner requested hardware functions first, software afterwards; preserve native
Lineage and Google features. Flash ready verified fixes automatically. No agents.

The next build is blocked by SSD read retries. Reconnect request pending. The
previous wsl--shutdown completed0; only an Ubuntu machine-id startup/read request
may remain hung (exec63889). No build is running. Start one distro at a time and
verify its machineid/root. UbuntuC:3fa9d65f37d2414bb2f2b18f86ca1736; T110BuildE:
cd27023803954a89ad7c30407399c847. Prefer cmd.exe/loginfalse until the Windows shell
recovers; use Python argument arrays for quoted commands. Do not reset user services.

1. Networking: patch0095 is BUILT/INSTALLED and71 kernel regressions pass. Android
accepts its UID rules. Next failure is networkAddInterface RemoteIO121, because
native MARK is missing. Kernel config also lacks CONNMARK and IDLETIMER. These
exist in the exact source. Candidate netd-targets.config and patch0096 enable them;
build_netd_targets_kernel.sh verifies the known source and builds out-netd-targets.
Run oldconfig/check the exact config diff, build, compare the actual installed
module runtime sections again and run netd_target_probe.c's10 revision checks
in a suitable virtual kernel, then package a NEW boot revision and install after
guards. Never rerun BOOT39 installer. Keep the same v34 system if modules remain
runtime-equivalent; avoid a redundant2GB transfer. Recheck ordinary-app DNS/HTTPS,
actual netd interface attachment/routes, native off/on and reconnect before PASS.
Do not leave manual routes or strip UID policy to hide a missing kernel feature.

2. Graphics: raw-gpu.json and raw-gpu-skia-state.json pass all6 cases in both
framebuffer and queued-image pixels. HWUI still fails; uniforms/bindings/blending
are correct and post-swap finish/readback is red. New gles_audit.c logs VBO payload
and forces a tiny pre-swap readback. It is source-only, not yet compiled. After
Linux recovers run build_gles_audit.sh, then build_interaction_audit.py --gles-layer
and ONE new labeled HWUI trace. A build manifest now rejects stale source/SO pairs.
If pre-swap readback is green but queued red, investigate KHR presentation/resolve;
if readback also red, decode actual vertex/color payload and replay preparation
order. Raw tests upload after clear/useProgram; HWUI prepares VBO before clear and
program creation. A commit callback is after swap and cannot settle that ordering.
Do not enable HWUI globally until real pixel/lifecycle/native-size checks pass.
The old gpu_readback_probe.cpp was clear/scissor-only, not a shader geometry proof.

3. Bluetooth: SDIO functions1/2/3 exist, no mbt8xxx/HCI/HAL/feature integration yet.
Current module build includes mbt8xxx. Audit matching H4 transport/vendor ABI and
reuse Android's native Bluetooth implementation; do not add a dummy adapter.
Camera raw capture is already demonstrated; adapt the native V4L2 provider/output
path. Audio88PM805, sensors and actual stock-working key LEDs remain incomplete.
Read button-lights.txt before guessing controls: sec_touchkey lacks brightness,
and the optional RT5033 touchkey regulator is not registered on this device.

Only after hardware: keyboard, native wallpapers, browser/Play, responsiveness,
themes and native Lineage features. Keep requested apps; GoogleAuto crashes on
the absent BluetoothAdapter and startup/JIT issues remain. Do not hide failures
by deleting apps, extending production ANR deadlines or calling clears a GPU pass.

Current boot a1d15767-b169-4593-818b-63132704d969/server311; BOOT39 SHA33462a6a2cffc1695ac8d8f986d42eac13b12b0708a5eb9db26f66c9baa73701.
BOOT38 rollback SHA b5bab81d2693d3b8b3e479963275173c938b3110e3110fa20489f72cae5694c5.
Systemv34 SHA9aaae33e0f8d52c65e46212842cfba82409a01cfe980356a11c668d4526a7151.
Recovery/data profiles preserved. Never write physicalSYSTEMp15. Temporary test
app removed; settings restored. Old v32 cleanup denials were not retried.
'''
(p/'RESUME-NEXT.md').write_text(resume,encoding='utf-8')
f=p/'FUNCTIONAL-CHECKLIST.md';s=f.read_text(encoding='utf-8')
updates={
 'CORE01':'- [x] **CORE01 Boot reaches Android and launcher - PASS**. v34 system with BOOT39 reaches unlocked Android; earlier launcher pass remains. BOOT39 startup227.89s; basic boot does not establish responsiveness. [evidence](evidence/hardware-v35/boot39-installation.json)',
 'CORE02':'- [ ] **CORE02 Startup completes without service ANRs or automatic restarts - FAIL**. BOOT39 completes startup in227.89s and retains system_server311, but Google/SystemUI startup and responsiveness issues remain. Test-app debug startup was corrected independently; it is not an OS performance fix. [evidence](evidence/hardware-v35/boot39-startup.txt), [evidence](evidence/hardware-v35/final-status.json)',
 'NET05':'- [ ] **NET05 DHCP, IP and default route - PARTIAL**. Authentication/DHCP persist. Patch0095 passes71 virtual-kernel regressions and Android now accepts UID rules. Actual interface attachment still fails RemoteIO121 at missing native MARK support; real routes then fail ENODEV19. The next target configuration is staged but unbuilt. [evidence](evidence/hardware-v35/boot39-connectivity.txt), [evidence](evidence/hardware-v35/netd-targets-source.json)',
 'NET06':'- [ ] **NET06 DNS and HTTPS internet access - FAIL**. Current ordinary-app hostname lookup fails on BOOT39. Native packet-marking support must be built before interface attachment/routes can succeed; no manual route workaround remains. [evidence](evidence/hardware-v35/final-app-network.txt)',
 'NET10':'- [ ] **NET10 Bluetooth adapter/driver/HAL available - FAIL**. Three SDIO functions are present, but mbt8xxx is not loaded and no BluetoothManager/HCI/HAL integration is active. Hardware transport presence is not a Bluetooth pass. [evidence](evidence/hardware-v35/bluetooth-transport.txt)',
 'LIGHT01':'- [ ] **LIGHT01 Capacitive Back/Recents key illumination - FAIL**. Owner confirms stock LEDs work. Current sec_touchkey has no brightness control; optional RT5033 touchkey regulator in board source is absent from the runtime inventory. No guessed rail writes were performed. [evidence](evidence/hardware-v35/button-lights.txt)',
}
for key,line in updates.items():
    s,count=re.subn(r'^- \[[ x]\] \*\*'+key+r' .*$',lambda match:line,s,flags=re.M);assert count==1,key
new='- [ ] **NET16 Wi-Fi identity and live link metrics - PARTIAL**. Association is real, but native dumps report unknown MAC/link-speed and RSSI -127; factory identity and useful signal reporting still need qualification. Do not infer factory MAC correctness from the template kernel address. [evidence](evidence/hardware-v35/final-wifi.txt)\n'
assert '**NET16 ' not in s
s=s.replace('## Storage',new+'\n## Storage',1) if '## Storage' in s else s+'\n'+new
counts=collections.Counter(re.findall(r'^- \[[ x]\] \*\*\w+ .*? - ([A-Z_]+)\*\*',s,re.M))
s=re.sub(r'^Counts:.*$','Counts: '+', '.join(k+'='+str(counts[k]) for k in sorted(counts))+'.',s,flags=re.M)
s=s.replace('[Current v34 result](evidence/offline-v41/gapps-v34-test/result.json).','[Current hardware checkpoint](evidence/hardware-v35/final-status.json).')
f.write_text(s,encoding='utf-8');record['checklist_counts']=dict(counts)
(e/'final-status.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,indent=2))
