from pathlib import Path
import subprocess
base=Path('/root/t110-build/lineage20/frameworks/base')
p=base/'services/core/jni/gnss/Android.bp';s=p.read_text();old='    name: "libservices.core-gnss",';assert s.count(old)==1;s=s.replace(old,old+'\n    shared_libs: ["libbase"],',1);p.write_text(s)
diff=subprocess.check_output(['git','-C',str(base),'diff','--binary'])
Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/patches/0040-gnss-t110-declared-service-probe.patch').write_bytes(diff)
print('Declared libbase dependency for the GNSS library')
