"""Opt in to lower Go GC heap growth for this memory-constrained build host."""
import difflib
import subprocess
from pathlib import Path
source = Path('/root/t110-build/lineage20/build/soong')
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
relative = 'ui/build/soong.go'
path = source / relative
old = subprocess.check_output(['git','-C',str(source),'show','HEAD:'+relative],text=True)
marker = '\tinvocationEnv := make(map[string]string)\n'
assert old.count(marker) == 1
new = old.replace(marker, marker + '\tif gc := os.Getenv("T110_SOONG_GOGC"); gc != "" {\n\t\tinvocationEnv["GOGC"] = gc\n\t}\n')
assert path.read_text() in [old,new]
patch = ''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+relative,tofile='b/'+relative))
out = project/'patches/0014-host-soong-gc-opt-in.patch'
out.write_text(patch)
subprocess.run(['git','-C',str(source),'apply','--cached','--check',str(out)],check=True)
path.write_text(new)
print(out)
