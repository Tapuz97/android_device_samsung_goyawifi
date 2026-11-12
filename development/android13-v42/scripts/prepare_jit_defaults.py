from pathlib import Path
import subprocess
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
repo=Path('/root/t110-build/lineage20/build/make')
p=repo/'target/product/runtime_libart.mk'
s=p.read_text()
assert 'dalvik.vm.usejit=true' in s and 'dalvik.vm.usejitprofiles=true' in s
s=s.replace('dalvik.vm.usejit=true','dalvik.vm.usejit?=true').replace('dalvik.vm.usejitprofiles=true','dalvik.vm.usejitprofiles?=true')
p.write_text(s)
diff=subprocess.check_output(['git','-C',str(repo),'diff','--','target/product/runtime_libart.mk'])
(project/'patches/0032-build-allow-device-jit-default-override.patch').write_bytes(diff)
print('Inherited JIT values converted to overridable defaults; other products retain true.')
