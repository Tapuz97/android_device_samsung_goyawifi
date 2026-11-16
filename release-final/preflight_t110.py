"""Read-only checks for this engineering layout. NEVER installs or writes firmware."""
import argparse
import json
import subprocess

def require(condition, message):
    if not condition: raise RuntimeError(message)

def check(adb, serial):
    def run(*args):
        p=subprocess.run([adb,'-s',serial,*args],capture_output=True,text=True,timeout=30)
        require(p.returncode==0,'ADB failed: '+p.stderr.strip())
        return p.stdout.strip().replace('\r','')
    require(run('get-state')=='recovery','Enter working TWRP first; no tablet changes made')
    require('uid=0' in run('shell','id'),'Root recovery ADB is required')
    model=run('shell','getprop ro.product.model')
    device=run('shell','getprop ro.product.device')
    require(model=='SM-T110' and device=='goyawifi','Wrong/unknown recovery identity; only SM-T110/goyawifi')
    sizes={name:int(run('shell','cat /sys/class/block/'+name+'/size'))
           for name in ('mmcblk0p9','mmcblk0p10','mmcblk0p16')}
    require(sizes=={'mmcblk0p9':32768,'mmcblk0p10':32768,'mmcblk0p16':10760192},'Partition geometry differs; stop')
    mounts=run('shell','cat /proc/mounts')
    require(any(line.startswith('/dev/block/mmcblk0p16 /data ext4 ') for line in mounts.splitlines()),
            'Physical userdata must be mounted as ext4 /data in TWRP; do not format it')
    require(run('shell','if [ -e /sys/block/loop0/loop/backing_file ]; then echo BUSY; else echo UNUSED; fi')=='UNUSED',
            'loop0 is in use; never replace an active system backing file')
    require(run('shell','if [ -L /data ] || [ -L /data/local ] || [ -L /data/local/tmp ]; then echo LINK; else echo OK; fi')=='OK',
            'Unexpected symlink in the target path')
    free=int(run('shell','/sbin/busybox df -Pk /data').splitlines()[-1].split()[3])*1024
    require(free>=2500*1024*1024,'Need at least2500MiB free for staging and a margin; do not delete the only rollback copy')
    result={'status':'PASS_READ_ONLY_PREFLIGHT_NOT_A_CLEAN_INSTALL_QUALIFICATION',
            'model':model,'device':device,'sector_counts':sizes,'free_bytes':free,'firmware_written':False}
    print(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--adb',default='adb')
    p.add_argument('--serial',required=True)
    args=p.parse_args()
    check(args.adb,args.serial)
