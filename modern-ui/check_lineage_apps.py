"""Compare built-in application sets in the actual old and new images."""
from pathlib import Path
import json,subprocess
WORK=Path('/root/t110-lineage14-ui')
old=Path('/root/t110-lineage14/artifacts/lineage14-first-build/system.raw.img')
new=WORK/'artifacts/system.raw.img'
def names(image,parent):
    data=subprocess.run(['debugfs','-R','ls -p /'+parent,str(image)],capture_output=True,text=True,check=True).stdout
    result={line.split('/')[5] for line in data.splitlines() if line.startswith('/') and len(line.split('/'))>6}
    result-={'.','..'}
    assert result,(image,parent)
    return result
entries=[]
for parent in ('app','priv-app'):
    before=names(old,parent);after=names(new,parent)
    entries.append({'path':parent,'old_count':len(before),'new_count':len(after),
                    'missing':sorted(before-after),'added':sorted(after-before)})
report={'status':'PASS' if all(not x['missing'] for x in entries) else 'MISSING_APPLICATIONS',
        'scope':'Built-in app directory sets in original working and new actual ext4 images',
        'directories':entries}
(WORK/'artifacts/app-preservation-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert report['status']=='PASS'
