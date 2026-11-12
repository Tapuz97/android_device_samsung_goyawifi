from pathlib import Path
import difflib,hashlib,json,os
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');root=Path('/root/t110-build/lineage20/hardware/interfaces');e=p/'evidence/hardware-bt-sd'
name='bluetooth/1.1/default/Android.bp';f=root/name;receipt=e/'hal-runpath-source.json';sha=lambda value:hashlib.sha256(value).hexdigest()
if receipt.exists():assert sha(f.read_bytes())==json.loads(receipt.read_text())['after_sha256'];print('HAL_RUNPATH_ALREADY_APPLIED');raise SystemExit(0)
before=f.read_text();marker='    relative_install_path: "hw",';assert before.count(marker)==1
after=before.replace(marker,marker+'''
    // The shared HCI implementation is installed under lib[64]/hw. Give
    // this executable its direct dependency path in legacy linker namespaces.
    // A service environment override is ignored on SELinux secure exec.
    multilib: {
        lib32: { ldflags: ["-Wl,-rpath,/vendor/lib/hw"] },
        lib64: { ldflags: ["-Wl,-rpath,/vendor/lib64/hw"] },
    },''')
patch=p/'patches/0104-bluetooth-service-find-installed-implementation.patch';assert not patch.exists();patch.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),'a/'+name,'b/'+name)))
f.write_text(after);receipt.write_text(json.dumps(dict(file=name,before_sha256=sha(before.encode()),after_sha256=sha(after.encode()),patch_sha256=sha(patch.read_bytes())),indent=2)+'\n');print('HAL_RUNPATH_SOURCE_READY')
