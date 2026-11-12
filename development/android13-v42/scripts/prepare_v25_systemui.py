"""Handle AppOpsService's valid null result without interrupting UI startup."""
from pathlib import Path
import subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
repo=Path('/root/t110-build/lineage20/frameworks/base')
name='packages/SystemUI/src/com/android/systemui/appops/AppOpsControllerImpl.java'
file=repo/name
old='        List<AppOpsManager.PackageOps> packageOps = mAppOps.getPackagesForOps(OPS);\n'
new=old+'''        // AppOpsService returns null when there are no recorded matching operations.
        // Live callbacks are already registered and must remain active on a fresh boot.
        if (packageOps == null) {
            return;
        }
'''
s=file.read_text(); assert s.count(old)==1 and new not in s
file.write_text(s.replace(old,new))
(p/'patches/0045-systemui-empty-active-appops.patch').write_bytes(subprocess.check_output(
    ['git','-C',str(repo),'diff','--',name]))
print('Prepared SystemUI null-result fix')
