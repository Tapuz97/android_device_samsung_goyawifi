from pathlib import Path
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/hardware-v35/boot41-init-sources';e.mkdir(exist_ok=True)
ns={'__file__':str(p/'scripts/verify_v28_boot.py')};exec((p/'scripts/verify_v28_boot.py').read_text().split('\nold = unpack(',1)[0],ns)
files=ns['unpack'](p/'artifacts/android13-boot-v41/KERNEL.img')[3]
for name,data in files.items():
 if name.endswith(('.rc','.sh')) or name in ('t110-stage','t110-full-stage'):
  print(name,len(data));(e/name.replace('/','_')).write_bytes(data)
