"""Upload private backup assets to the existing draft, then hash downloaded bytes."""
from pathlib import Path
import subprocess,json,hashlib,urllib.request,urllib.error,sys
r=Path(__file__).resolve().parents[1];out=r/'backups/android13-before-lineage14-20261112'
settings=json.loads((r/'community/private-draft-backup.json').read_text())
repo=settings['repository'];tag=settings['tag'];releaseid=settings['release_id']
assert settings['draft'] and not settings['published']
statefile=out/'online-backup-verification.json'
state=json.loads(statefile.read_text()) if statefile.exists() else {'repository':repo,'release_id':releaseid,'draft':True,'assets':{}}
def gh(*args):return json.loads(subprocess.check_output(['gh','api',*args],text=True))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
for filename in sys.argv[1:]:
 p=Path(filename).resolve();assert p.is_file() and p.is_relative_to(out)
 digest=sha(p);size=p.stat().st_size;assert size<2*1024**3
 release=gh(f'repos/{repo}/releases/{releaseid}')
 assert release['draft'] and release['published_at'] is None
 existing=next((a for a in release['assets'] if a['name']==p.name),None)
 if not existing:
  print('UPLOADING',p.name,size,flush=True)
  subprocess.run(['gh','release','upload',tag,str(p),'--repo',repo],check=True)
  release=gh(f'repos/{repo}/releases/{releaseid}')
  existing=next(a for a in release['assets'] if a['name']==p.name)
 assert existing['size']==size and existing['digest']=='sha256:'+digest,existing['name']
 access_checks={}
 for label,url in [('api',existing['url']),('browser',existing['browser_download_url'])]:
  rate_limited=False
  try:
   with urllib.request.urlopen(url,timeout=30) as response:status=response.status
  except urllib.error.HTTPError as e:
   status=e.code
   rate_limited=(label=='api' and status==403 and e.headers.get('X-RateLimit-Remaining')=='0')
  access_checks[label]={'status':status,'rate_limited':rate_limited}
  assert status==404 or rate_limited,('Anonymous access check inconclusive or unexpectedly public',p.name,label,status)
 assert access_checks['browser']['status']==404
 prior=state['assets'].get(p.name)
 if prior and prior['sha256']==digest and prior.get('download_sha256_verified'):
  print('ALREADY_VERIFIED',p.name,flush=True);continue
 print('DOWNLOADING_AND_HASHING',p.name,flush=True)
 proc=subprocess.Popen(['gh','release','download',tag,'--repo',repo,'--pattern',p.name,'--output','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 h=hashlib.sha256();received=0
 while True:
  b=proc.stdout.read(8*1024*1024)
  if not b:break
  h.update(b);received+=len(b)
 error=proc.stderr.read();rc=proc.wait()
 assert rc==0,(p.name,error.decode(errors='replace'))
 assert received==size and h.hexdigest()==digest,(p.name,received,h.hexdigest())
 state['assets'][p.name]={'id':existing['id'],'bytes':size,'sha256':digest,
  'github_digest_verified':True,'download_sha256_verified':True,'anonymous_access_http':404,
  'anonymous_access_checks':access_checks,'state':existing['state']}
 statefile.write_text(json.dumps(state,indent=2)+'\n')
 print('VERIFIED_ONLINE',p.name,digest,flush=True)
print('Verified asset count',len(state['assets']),flush=True)
