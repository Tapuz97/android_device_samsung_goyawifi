"""Prepare source fixes on the available internal checkout; no device writes."""
from pathlib import Path
import subprocess,json,hashlib
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
t=Path('/root/t110-build/lineage20');e=p/'evidence/remote-fixes-20261110'
e.mkdir(exist_ok=True)
def run(args):return subprocess.run(list(map(str,args)),capture_output=True,check=True).stdout
def patch(repo,name):
    data=(p/'patches'/name).read_bytes()
    if subprocess.run(['git','-C',str(t/repo),'apply','--reverse','--check','-'],input=data,capture_output=True).returncode==0:return
    subprocess.run(['git','-C',str(t/repo),'apply','--check','-'],input=data,capture_output=True,check=True)
    subprocess.run(['git','-C',str(t/repo),'apply','-'],input=data,capture_output=True,check=True)
def export(repo,rel,name,before):
    after=(t/repo/rel).read_text()
    import difflib
    diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
    assert diff
    (p/'patches'/name).write_text(diff)

repo='lineage-sdk';rel='sdk/src/java/lineageos/hardware/LineageHardwareManager.java'
f=t/repo/rel;before=f.read_text()
assert 'optional_hal_probe' not in before
after=before.replace('import android.os.ServiceManager;','import android.os.ServiceManager;\nimport android.os.SystemProperties;')
anchor='    private IBase getHIDLService(int feature) {\n        try {'
assert anchor in after
after=after.replace(anchor,'''    private IBase getHIDLService(int feature) {
        // This pre-Treble product does not declare optional Lineage HALs.
        // Do not block IMMS/system_server waiting for absent touch/display
        // extensions. getService(false) still discovers an available HAL;
        // isSupported() retains its existing HWC2 fallback.
        final boolean retry = !SystemProperties.getBoolean("ro.t110.optional_hal_probe", false);
        try {''')
assert after.count('.getService(true)')==16
after=after.replace('.getService(true)','.getService(retry)');f.write_text(after)
export(repo,rel,'0077-lineage-sdk-t110-nonblocking-hardware-probes.patch',before)

patch('frameworks/native','0048-gralloc-t110-process-initialization.patch')
repo='frameworks/native';rel='libs/ui/Gralloc2.cpp';f=t/repo/rel;before=f.read_text()
anchor='''status_t Gralloc2Mapper::importBuffer(const hardware::hidl_handle& rawHandle,
                                      buffer_handle_t* outBufferHandle) const {
    Error error;'''
assert anchor in before
after=before.replace(anchor,'''status_t Gralloc2Mapper::importBuffer(const hardware::hidl_handle& rawHandle,
                                      buffer_handle_t* outBufferHandle) const {
    // Import-only clients (notably screencap's binder callback) may never
    // allocate a buffer or initialize EGL. registerBuffer still needs this
    // Vivante driver's process-local OS/GPU state before importing handles.
    auto& legacy = T110LegacyAllocation::get();
    if (legacy.enabled() && !legacy.ready()) return NO_INIT;
    Error error;''')
f.write_text(after)
export(repo,rel,'0078-gralloc-t110-initialize-import-only-clients.patch',before)

src=p/'work/core-boot/ion_alloc_probe.c';out=e/'ion-alloc-probe'
run(['arm-linux-gnueabi-gcc','-static','-O2','-march=armv7-a','-mfloat-abi=soft','-Wall','-Wextra','-Werror',src,'-o',out])
record={'source_root':str(t),'build_drive':'Ubuntu internal C drive; E unavailable','source_revisions':{r:run(['git','-C',t/r,'rev-parse','HEAD']).decode().strip() for r in ['lineage-sdk','frameworks/native','frameworks/av']},'probe_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'firmware_built':False,'firmware_installed':False}
(e/'source-preparation.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
