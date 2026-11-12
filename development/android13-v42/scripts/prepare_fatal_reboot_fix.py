from pathlib import Path
import difflib
root=Path('/root/t110-build/lineage20/system/core')
p=root/'init/reboot_utils.cpp'
before=p.read_text()
old='start_pos += sizeof(kRebootTargetStringPattern) - 1;'
assert before.count(old)==1
after=before.replace(old,'start_pos += kRebootTargetStringPattern.size();')
p.write_text(after)
patch=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/patches/0026-init-fatal-reboot-target-length.patch')
patch.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/init/reboot_utils.cpp',tofile='b/init/reboot_utils.cpp')))
print('Fatal reboot target uses string length, not sizeof(std::string)')
