"""Fetch only relevant files from the exact published kernel baseline."""
from pathlib import Path
import concurrent.futures,gzip,hashlib,json,re,urllib.request
p=Path(__file__).resolve().parents[1];out=p/'evidence/hardware-v35/upstream-kernel';out.mkdir(exist_ok=True)
revision='3c50b450af74d42f8c5d360c692f71002b3bb0af'
root='https://raw.githubusercontent.com/visyone/android_kernel_samsung_goya/'+revision+'/'
files=['net/netfilter/Kconfig','net/netfilter/xt_mark.c','net/netfilter/xt_IDLETIMER.c',
       'include/linux/netfilter/xt_IDLETIMER.h','arch/arm/mach-mmp/board-goya.c']
request=urllib.request.Request('https://api.github.com/repos/visyone/android_kernel_samsung_goya/git/trees/'+revision+'?recursive=1',headers={'User-Agent':'T110-hardware-source-audit'})
try:
    tree=json.loads(urllib.request.urlopen(request,timeout=25).read())
    selected=[row['path'] for row in tree['tree'] if row['type']=='blob' and row['path'].startswith('drivers/input/')
              and re.search('zinitix|bt532|touchkey',row['path'],re.I) and 'firmware' not in row['path'].lower()]
    (out/'input-source-paths.json').write_text(json.dumps(selected,indent=2)+'\n')
    files+=selected
except Exception as error:print('Tree lookup:',type(error).__name__,str(error)[:100],flush=True)
def fetch(name):
    try:
        data=urllib.request.urlopen(root+name,timeout=20).read()
        target=out/name;assert out.resolve() in target.resolve().parents
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        return name,{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    except Exception as error:return name,{'error':str(error)[:140]}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records=dict(pool.map(fetch,files))
(out/'source-manifest.json').write_text(json.dumps({'revision':revision,'root':root,'files':records},indent=2)+'\n')
config=gzip.decompress((out.parent/'boot39-config.gz').read_bytes());(out.parent/'boot39.config').write_bytes(config)
print('Saved',len(records),'selected source files; running config SHA256',hashlib.sha256(config).hexdigest())
for name in files:print(name,records[name].get('bytes',records[name].get('error')))
