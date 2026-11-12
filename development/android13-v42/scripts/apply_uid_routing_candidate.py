"""Apply only reviewed candidate files whose base or prior candidate is known."""
from pathlib import Path
import difflib,hashlib,json,subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
work=Path('/root/t110-build/uid-routing-backport');src=work.parent/'kernel-display-i2c'
record_path=p/'evidence/hardware-v35/uid-source.json'
record=json.loads(record_path.read_text());patch=[]
for item in record['files']:
    name=item['path'];f=src/name;candidate=work/'candidate'/name
    current=f.read_text();after=candidate.read_text()
    # All source mutations are restricted to the saved base/candidate set.
    assert (work/'base'/name).is_file()
    digest=hashlib.sha256(f.read_bytes()).hexdigest()
    assert digest in (record.get('allowed_current_hashes',{}).get(name),item['before_sha256'],item['after_sha256']), 'Unreviewed source edit: '+name
    patch.extend(difflib.unified_diff(current.splitlines(True),after.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
diff=''.join(patch)
if diff:
    subprocess.run(['patch','--dry-run','-p1'],cwd=src,input=diff,text=True,check=True)
    subprocess.run(['patch','-p1'],cwd=src,input=diff,text=True,check=True)
for item in record['files']:
    assert hashlib.sha256((src/item['path']).read_bytes()).hexdigest()==item['after_sha256']
record['status']='APPLIED_BUILD_PENDING';record_path.write_text(json.dumps(record,indent=2)+'\n')
print('UID_CANDIDATE_SOURCE_MATCHES_RECORD')
