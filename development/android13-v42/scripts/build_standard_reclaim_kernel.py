"""Keep the qualified hardware configuration; restore normal compressed-swap reclaim."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
assert os.environ.get('WSL_DISTRO_NAME')=='Ubuntu'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/ui-system-hang-20261112'
base=Path('/root/t110-build');src=base/'kernel-display-i2c';parent=base/'out-gateway';out=base/'out-standard-reclaim'
assert not out.exists(),'Inspect an incomplete kernel build before retrying'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(parent/'.config')==json.loads((p/'artifacts/android13-boot-v46/provenance.json').read_text())['kernel_config_sha256']
subprocess.run(['cp','-a','--reflink=auto',str(parent),str(out)],check=True)
old=(out/'.config').read_text();assert 'CONFIG_ZRAM_FOR_ANDROID=y' in old and 'CONFIG_ZRAM_FOR_RTCC2=y' in old
subprocess.run([str(src/'scripts/config'),'--file',str(out/'.config'),'-d','ZRAM_FOR_ANDROID','-d','ZRAM_FOR_RTCC2'],check=True)
new=(out/'.config').read_text()
assert new==old.replace('CONFIG_ZRAM_FOR_ANDROID=y','# CONFIG_ZRAM_FOR_ANDROID is not set').replace('CONFIG_ZRAM_FOR_RTCC2=y','# CONFIG_ZRAM_FOR_RTCC2 is not set')
assert 'CONFIG_SWAP=y\n' in new and 'CONFIG_ZRAM=y\n' in new
(e/'kernel-standard-reclaim.config').write_text(new)
record=dict(status='BUILDING',parent_config_sha256=sha(parent/'.config'),config_sha256=sha(out/'.config'),
            changed_options={'CONFIG_ZRAM_FOR_ANDROID':'n','CONFIG_ZRAM_FOR_RTCC2':'n'},normal_zram_enabled=True,
            reason='Legacy Android option forces may_swap=0 in normal direct/kswapd reclaim; actual swap unused despite file-cache thrashing',
            source_vmscan_sha256=sha(src/'mm/vmscan.c'),output=str(out),modules_verified=False)
(e/'kernel-standard-reclaim.json').write_text(json.dumps(record,indent=2)+'\n')
make=['make','-j2','ARCH=arm','CROSS_COMPILE='+str(base/'toolchain/bin/arm-eabi-'),'O='+str(out)]
started=time.monotonic();print('STANDARD_RECLAIM_KERNEL_BUILD_STARTED',flush=True)
with (e/'kernel-standard-reclaim-build.log').open('wb') as log:
    r=subprocess.run(make+['olddefconfig'],cwd=src,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode!=0:
        # This Samsung 3.4 tree may predate olddefconfig. oldconfig has no new
        # unknown settings because this is an exact qualified config copy.
        r=subprocess.run(make+['oldconfig'],cwd=src,input=b'\n'*128,stdout=log,stderr=subprocess.STDOUT)
    assert r.returncode==0
    assert (out/'.config').read_text()==new,'Configuration changed beyond the two intended options'
    r=subprocess.run(make+['zImage','modules'],cwd=src,stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0,('Kernel build failed',r.returncode)
assert (out/'.config').read_text()==new
dest=e/'standard-reclaim-components';dest.mkdir(exist_ok=True)
shutil.copyfile(out/'arch/arm/boot/zImage',dest/'zImage');shutil.copyfile(out/'.config',dest/'kernel.config')
record.update(status='KERNEL_COMPILED_MODULE_QUALIFICATION_PENDING',seconds=round(time.monotonic()-started,2),kernel_sha256=sha(dest/'zImage'))
(e/'kernel-standard-reclaim.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
