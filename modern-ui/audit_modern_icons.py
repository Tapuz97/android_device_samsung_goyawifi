"""Locate immutable official Lineage launcher artwork; no tablet access."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, subprocess
DEST=Path(r'\\wsl.localhost\Ubuntu\root\t110-lineage14-ui\icon-reference')
DEST.mkdir(exist_ok=True)
names=['ExactCalculator','Etar','Contacts','DeskClock','Glimpse','Eleven',
       'Recorder','AudioFX','Jelly','Aperture','Settings','Email']
repos=['android_packages_apps_'+x for x in names]+['android_packages_modules_DocumentsUI']
def fetch(repo):
    p=subprocess.run(['gh','api','repos/LineageOS/'+repo+'/git/trees/HEAD?recursive=1'],
                     capture_output=True,encoding='utf-8')
    if p.returncode:return repo,{'error':'No accessible default tree'}
    data=json.loads(p.stdout)
    candidates=[x for x in data['tree'] if x['type']=='blob'
                and ('ic_launcher' in x['path'] or 'ic_app_icon' in x['path']
                     or x['path'].split('/')[-1] in ('LICENSE','COPYING','NOTICE','AndroidManifest.xml'))]
    return repo,{'tree_sha':data['sha'],'files':candidates}
with ThreadPoolExecutor(max_workers=4) as executor:records=dict(executor.map(fetch,repos))
(DEST/'catalog.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
for repo,record in records.items():
    print(repo,record.get('error',''))
    for entry in record.get('files',[]):
        if 'ic_launcher' in entry['path'] or 'ic_app_icon' in entry['path']:print(' ',entry['path'])
