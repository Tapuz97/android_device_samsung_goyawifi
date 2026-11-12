from pathlib import Path
import json,struct
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
ns={'__file__':str(p/'scripts/verify_v28_boot.py')};exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
boot=ns['unpack'](p/'artifacts/android13-boot-v42/KERNEL.img')
names={name:len(data) for name,data in boot[3].items() if any(key in name for key in ['policy','context','fstab','uevent'])}
print(json.dumps(names,indent=2))
policy=boot[3]['t110-preload-policy'];length=struct.unpack_from('<I',policy,4)[0]
print('POLICY_IDENTIFIER',policy[8:8+length].decode(),'VERSION',struct.unpack_from('<I',policy,8+length)[0])
