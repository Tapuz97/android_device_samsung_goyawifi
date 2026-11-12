from pathlib import Path
import re,subprocess,json,hashlib
root=Path('/root/t110-build/stock-system-files');out=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/stock/T110XXUANI7')
roots=sorted(list((root/'lib/hw').glob('*.so'))+list((root/'lib/egl').glob('*.so')))
queue=list(roots);seen={}
while queue:
 p=queue.pop(0);rel=str(p.relative_to(root))
 if rel in seen:continue
 raw=subprocess.check_output(['readelf','-d',str(p)],text=True,stderr=subprocess.DEVNULL)
 deps=re.findall(r'Shared library: \[(.*?)\]',raw)
 seen[rel]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'needed':deps}
 for dep in deps:
  candidate=root/'lib'/dep
  if candidate.exists():queue.append(candidate)
report={'origin':'Verified matching AP archive, not tablet dump','root_modules':[str(p.relative_to(root)) for p in roots],'libraries':seen,'warning':'Dependency closure describes stock Android ABI; these libraries must not overwrite Android 13 platform libraries.'}
(out/'archive-hal-dependency-closure.json').write_text(json.dumps(report,indent=2));print('HAL/EGL roots',len(roots),'dependency closure libraries',len(seen))
