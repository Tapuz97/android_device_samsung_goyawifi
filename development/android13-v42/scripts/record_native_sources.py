import json,subprocess
from pathlib import Path
root=Path('/root/t110-build/lineage20')
paths=subprocess.check_output([str(root/'.repo/repo/repo'),'list','-p'],cwd=root,text=True).splitlines()
projects=[]
for name in paths:
 rev=subprocess.check_output(['git','-C',str(root/name),'rev-parse','HEAD'],text=True).strip()
 projects.append({'path':name,'revision':rev})
result={'kind':'partial native Android 13 checkout, not complete ROM source lock','manifest_revision':'0d12a657c699970c9f0a82361eb170aa9ccaeb59','projects':projects}
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/evidence/android13-native-source-pins.json')
p.write_text(json.dumps(result,indent=2)+'\n')
print('Recorded',len(projects),'native source revisions')
