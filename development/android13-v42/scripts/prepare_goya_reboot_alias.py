"""Accept Android's bootloader reboot target as Samsung's existing download target."""
from pathlib import Path
import difflib, hashlib, json, subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
root=Path('/root/t110-build/kernel-display-i2c')
f=root/'arch/arm/mach-mmp/board-goya.c'
before=f.read_text()
old='!strcmp(cmd,"download")'
new='(!strcmp(cmd,"download") || !strcmp(cmd,"bootloader"))'
patch=p/'patches/0085-kernel-goya-android-bootloader-reboot-alias.patch'
if new not in before:
    assert before.count(old)==3, before.count(old)
    after=before.replace(old,new)
    diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/arch/arm/mach-mmp/board-goya.c',tofile='b/arch/arm/mach-mmp/board-goya.c'))
    assert not patch.exists() or patch.read_text()==diff
    patch.write_text(diff)
    subprocess.run(['patch','--dry-run','-p1'],cwd=root,input=diff,text=True,check=True)
    subprocess.run(['patch','-p1'],cwd=root,input=diff,text=True,check=True)
else:
    after=before
    assert after.count(new)==3
    subprocess.run(['patch','--dry-run','-R','-p1'],cwd=root,input=patch.read_text(),text=True,check=True)
record={'status':'SOURCE_READY_NOT_TARGET_TESTED','source':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'behavior':'bootloader uses the existing Samsung download PMIC reason; recovery and other reasons unchanged','patched_download_branches':3}
(p/'evidence/offline-v41/reboot-alias-source.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
