from pathlib import Path
import subprocess,hashlib,json
root=Path('/root/t110-build/export-lineage20-rom-v7')
def content(name):
    return subprocess.check_output(['debugfs','-R','cat '+name,str(root/'system.raw.img')],stderr=subprocess.DEVNULL)
ui=content('/system/lib/libui.so')
cil=content('/system/vendor/etc/selinux/vendor_sepolicy.cil')
assert b'T110 legacy gralloc: retaining allocation owners in process' in ui
assert b'sysfs_t110_vsync' in cil and b'pxa168-fb.0/graphics/fb0/vsync_ts' in cil
result=dict(status='PASS',libui_sha256=hashlib.sha256(ui).hexdigest(),retained_owners_present=True,display_timestamp_label_present=True)
Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/evidence/v7-graphics-image-contents.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
