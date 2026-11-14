"""Apply only onto the recorded working14.1 baseline; fail before any write on mismatch."""
from pathlib import Path
import hashlib,json,sys
bundle=Path(__file__).resolve().parent
source=Path(sys.argv[1]).resolve()
files=json.loads((bundle/'files.json').read_text())
pending=[]
for name,record in files.items():
    target=source/name
    actual=hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
    if actual==record['sha256']:continue
    assert actual==record['before_sha256'], 'Baseline mismatch: '+name
    data=(bundle/'source'/name).read_bytes()
    assert hashlib.sha256(data).hexdigest()==record['sha256'], 'Bundle mismatch: '+name
    pending.append((target,data))
for target,data in pending:
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
print('Applied',len(pending),'native UI files. Build a complete system image before installation.')
