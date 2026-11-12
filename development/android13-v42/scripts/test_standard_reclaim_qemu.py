"""Boot the same kernel source's standard reclaim path in an isolated ARM guest."""
from pathlib import Path
import json,os,shutil,subprocess,time
assert os.environ.get('WSL_DISTRO_NAME')=='Ubuntu'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/ui-system-hang-20261112'
base=Path('/root/t110-build');src=base/'kernel-display-i2c';out=base/'out-qemu-standard-reclaim'
assert not out.exists(),'Inspect an incomplete QEMU build before restarting'
subprocess.run(['cp','-a','--reflink=auto',str(base/'out-qemu-netd-targets'),str(out)],check=True)
subprocess.run([str(src/'scripts/config'),'--file',str(out/'.config'),'-e','STAGING','-e','ZRAM','-d','ZRAM_FOR_ANDROID','-d','ZRAM_FOR_RTCC2'],check=True)
make=['make','-j2','ARCH=arm','CROSS_COMPILE='+str(base/'toolchain/bin/arm-eabi-'),'O='+str(out)]
print('QEMU_STANDARD_RECLAIM_BUILD_STARTED',flush=True)
with (e/'qemu-standard-reclaim-build.log').open('wb') as log:
    r=subprocess.run(make+['oldconfig'],cwd=src,input=b'\n'*256,stdout=log,stderr=subprocess.STDOUT);assert r.returncode==0
    config=(out/'.config').read_text();assert 'CONFIG_ZRAM=y\n' in config and 'CONFIG_SWAP=y\n' in config
    assert 'CONFIG_ZRAM_FOR_ANDROID=y' not in config and 'CONFIG_ZRAM_FOR_RTCC2=y' not in config
    r=subprocess.run(make+['zImage'],cwd=src,stdout=log,stderr=subprocess.STDOUT);assert r.returncode==0
root=base/'qemu-standard-reclaim-guest';assert not root.exists();root.mkdir()
for name in ['dev','proc','sys']:(root/name).mkdir()
subprocess.run(['arm-linux-gnueabi-gcc','-static','-O2','-Wall','-Wextra','-Werror',str(p/'scripts/reclaim_swap_guest.c'),'-o',str(root/'init')],check=True)
subprocess.run(['mknod',str(root/'dev/console'),'c','5','1'],check=True)
names=b'\0'.join(str(f.relative_to(root)).encode() for f in sorted(root.rglob('*')))+b'\0'
archive=subprocess.run(['cpio','--quiet','-o','-0','-H','newc','--owner=0:0'],cwd=root,input=names,capture_output=True,check=True).stdout
import gzip
initrd=base/'qemu-standard-reclaim-guest.cpio.gz';initrd.write_bytes(gzip.compress(archive,mtime=0))
command=['qemu-system-arm','-M','vexpress-a9','-cpu','cortex-a9','-smp','2','-m','128M','-display','none','-monitor','none','-serial','stdio','-net','none','-no-reboot',
         '-kernel',str(out/'arch/arm/boot/zImage'),'-initrd',str(initrd),'-append','console=ttyAMA0 rdinit=/init panic=1']
started=time.monotonic()
r=subprocess.run(command,env={**os.environ,'QEMU_AUDIO_DRV':'none'},capture_output=True,timeout=180)
text=(r.stdout+r.stderr).decode(errors='replace');(e/'qemu-standard-reclaim.log').write_text(text)
record=dict(status='PASS' if r.returncode==0 and 'RECLAIM_SWAP_PASS ' in text and 'RECLAIM_SWAP_FAIL ' not in text else 'FAIL',
            seconds=round(time.monotonic()-started,2),guest_ram_mib=128,anonymous_allocation_mib=160,swap_mib=128,
            same_mm_source=True,samsung_hardware_emulated=False,tablet_access=False,exit_code=r.returncode,
            results=[line for line in text.splitlines() if 'RECLAIM_SWAP_' in line])
(e/'qemu-standard-reclaim.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
assert record['status']=='PASS'
