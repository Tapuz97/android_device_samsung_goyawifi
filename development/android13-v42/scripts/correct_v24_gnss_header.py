from pathlib import Path
import subprocess
p=Path('/root/t110-build/lineage20/frameworks/base/services/core/jni/gnss/Gnss.cpp')
s=p.read_text().replace('#include <hidl/ServiceManagement.h>', '#include <android/hidl/manager/1.0/IServiceManager.h>\n#include <hidl/ServiceManagement.h>')
s=s.replace('const auto transport = manager->getTransport', 'auto transport = manager->getTransport')
p.write_text(s)
diff=subprocess.check_output(['git','-C','/root/t110-build/lineage20/frameworks/base','diff','--binary'])
Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/patches/0040-gnss-t110-declared-service-probe.patch').write_bytes(diff)
print('GNSS complete type included; Return transport remains consumable')
