"""Save official icon XML and licenses with immutable Git blob provenance."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import base64, hashlib, json, subprocess
ROOT=Path(r'\\wsl.localhost\Ubuntu\root\t110-lineage14-ui\icon-reference')
catalog=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
jobs=[(repo,x) for repo,r in catalog.items() for x in r.get('files',[])
      if ('ic_launcher' in x['path'] and x['path'].endswith('.xml'))
      or x['path'].split('/')[-1] in ('LICENSE','COPYING','NOTICE')]
def fetch(job):
    repo,item=job
    p=subprocess.run(['gh','api','repos/LineageOS/'+repo+'/git/blobs/'+item['sha']],
                     capture_output=True,encoding='utf-8',check=True)
    result=json.loads(p.stdout);data=base64.b64decode(result['content'])
    target=ROOT/'upstream'/repo/item['path']
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return {'repo':'LineageOS/'+repo,'path':item['path'],'blob_sha':item['sha'],
            'sha256':hashlib.sha256(data).hexdigest(),
            'source':'https://api.github.com/repos/LineageOS/'+repo+'/git/blobs/'+item['sha']}
with ThreadPoolExecutor(max_workers=4) as executor:records=list(executor.map(fetch,jobs))
(ROOT/'download-provenance.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('Saved',len(records),'official resources/license files.')
