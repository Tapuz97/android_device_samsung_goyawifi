"""Verify changed-project base commits exist at their recorded upstreams."""
from pathlib import Path
import json,xml.etree.ElementTree as ET,subprocess,urllib.request,concurrent.futures
r=Path(__file__).resolve().parents[1];out=r/'backups/android13-before-lineage14-20261112'
manifest=ET.parse(out/'lineage20-source-delta/pinned-manifest.xml').getroot()
remotes={x.attrib['name']:x.attrib for x in manifest.findall('remote')};default=manifest.find('default').attrib
projects={x.attrib.get('path',x.attrib['name']):x.attrib for x in manifest.findall('project')}
records=json.loads((out/'lineage20-source-delta/projects.json').read_text());dirty=[x for x in records if x.get('diff_bytes') or x.get('untracked')]
def verify(item):
 entry=projects[item['path']];remote=remotes[entry.get('remote',default['remote'])]
 fetch=remote['fetch'];name=entry['name'];head=item['head']
 if 'github.com' in fetch or fetch in {'..','.'}:
  response=json.loads(subprocess.check_output(['gh','api',f'repos/{name}/git/commits/{head}'],text=True,stderr=subprocess.PIPE))
  assert response['sha']==head
  url='https://github.com/'+name+'/commit/'+head
 else:
  url=fetch.rstrip('/')+'/'+name+'/+/'+head+'?format=JSON'
  with urllib.request.urlopen(url,timeout=30) as response:raw=response.read().decode()
  response=json.loads(raw[4:] if raw.startswith(")]}'") else raw)
  assert response.get('commit')==head
 return {'path':item['path'],'head':head,'url':url,'upstream_verified':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(verify,dirty))
(out/'changed-project-bases-online.json').write_text(json.dumps({'status':'ALL_CHANGED_BASE_COMMITS_VERIFIED_ONLINE','count':len(result),'projects':result},indent=2)+'\n')
print('VERIFIED_UPSTREAM_COMMITS',len(result),flush=True)
