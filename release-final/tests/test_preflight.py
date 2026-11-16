"""Fault cases for the read-only checks used before manual firmware writes."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import contextlib
import io
import sys
sys.path.insert(0,str(Path(__file__).parent.parent))
import preflight_t110

GOOD={
 ('get-state',):'recovery',('shell','id'):'uid=0(root)',
 ('shell','getprop ro.product.model'):'SM-T110',('shell','getprop ro.product.device'):'goyawifi',
 ('shell','cat /sys/class/block/mmcblk0p9/size'):'32768',
 ('shell','cat /sys/class/block/mmcblk0p10/size'):'32768',
 ('shell','cat /sys/class/block/mmcblk0p16/size'):'10760192',
 ('shell','cat /proc/mounts'):'/dev/block/mmcblk0p16 /data ext4 rw 0 0',
 ('shell','if [ -e /sys/block/loop0/loop/backing_file ]; then echo BUSY; else echo UNUSED; fi'):'UNUSED',
 ('shell','if [ -L /data ] || [ -L /data/local ] || [ -L /data/local/tmp ]; then echo LINK; else echo OK; fi'):'OK',
 ('shell','/sbin/busybox df -Pk /data'):'Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/block/mmcblk0p16 5373980 1000000 4373980 19% /data'}

def attempt(overrides):
    fixture=GOOD|overrides
    seen=[]
    def fake(args,**kwargs):
        assert args[:3]==['adb','-s','test-only']
        key=tuple(args[3:]);seen.append(key)
        assert key in fixture,'Unexpected command, including any mutation: '+str(key)
        return SimpleNamespace(returncode=0,stdout=fixture[key],stderr='')
    with patch('preflight_t110.subprocess.run',side_effect=fake),contextlib.redirect_stdout(io.StringIO()):
        return preflight_t110.check('adb','test-only')

assert attempt({})['firmware_written'] is False
bad=[{('get-state',):'device'},
     {('shell','getprop ro.product.model'):'SM-T210'},
     {('shell','cat /sys/class/block/mmcblk0p10/size'):'16384'},
     {('shell','cat /proc/mounts'):'/dev/block/mmcblk0p16 /data f2fs rw 0 0'},
     {('shell','if [ -e /sys/block/loop0/loop/backing_file ]; then echo BUSY; else echo UNUSED; fi'):'BUSY'},
     {('shell','if [ -L /data ] || [ -L /data/local ] || [ -L /data/local/tmp ]; then echo LINK; else echo OK; fi'):'LINK'},
     {('shell','/sbin/busybox df -Pk /data'):'Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/block/mmcblk0p16 5373980 5000000 373980 93% /data'}]
for fixture in bad:
    try:attempt(fixture)
    except RuntimeError:pass
    else:raise AssertionError('Dangerous preflight mismatch accepted')
print('PASS: valid read-only fixture and7 wrong-state/model/geometry/filesystem/loop/symlink/space rejection cases; no tablet accessed.')
