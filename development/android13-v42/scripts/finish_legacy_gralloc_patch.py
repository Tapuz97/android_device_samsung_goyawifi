from pathlib import Path
import subprocess
repo=Path('/root/t110-build/lineage20/frameworks/native')
bp=repo/'libs/ui/Android.bp'
s=bp.read_text()
a='        "libcutils",\n        "libgralloctypes",'
assert s.count(a)==1 and '        "libhardware",' not in s
bp.write_text(s.replace(a,a+'\n        "libhardware",'))
patch=subprocess.check_output(['git','-C',str(repo),'diff','--','libs/ui/Gralloc2.cpp','libs/ui/Android.bp'])
Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/patches/0030-ui-t110-retained-gralloc-owners.patch').write_bytes(patch)
print('Patch exported')
