from pathlib import Path
import json,os
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');root=Path('/root/t110-build/lineage20');out=p/'evidence/hardware-bt-sd/android-source';out.mkdir(exist_ok=True)
paths=['hardware/interfaces/bluetooth/1.0/default/'+x for x in ['vendor_interface.cc','vendor_interface.h','bluetooth_hci.cc','Android.bp','service.cpp']]
paths+=['hardware/interfaces/bluetooth/1.1/default/'+x for x in ['Android.bp','bluetooth_hci.cc','service.cpp']]
paths+=['hardware/libhardware/include/hardware/bt_vendor_lib.h','system/core/fs_mgr/fs_mgr_fstab.cpp','system/vold/main.cpp']
record={}
for name in paths:
 f=root/name
 if not f.is_file():record[name]='MISSING';continue
 dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes());record[name]=f.stat().st_size
(out/'sources.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
