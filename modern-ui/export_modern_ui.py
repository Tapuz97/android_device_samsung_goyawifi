"""Export a self-contained native UI patch on top of the preserved bring-up."""
from pathlib import Path
import difflib,hashlib,json,shutil
SRC=Path('/root/t110-lineage14/android');WORK=Path('/root/t110-lineage14-ui')
DEST=WORK/'device/modern-ui';DEST.mkdir(exist_ok=True)
files=json.loads((WORK/'changed-files.json').read_text())
patch=[]
for name,entry in sorted(files.items()):
    now=(SRC/name).read_bytes()
    assert hashlib.sha256(now).hexdigest()==entry['sha256'],name
    target=DEST/'source'/name;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(now)
    if entry['before_sha256'] is not None:
        before=(WORK/'before'/name).read_bytes()
        assert hashlib.sha256(before).hexdigest()==entry['before_sha256'],name
        original=DEST/'before'/name;original.parent.mkdir(parents=True,exist_ok=True)
        original.write_bytes(before)
        if name.endswith(('.java','.xml')):
            patch.extend(difflib.unified_diff(before.decode().splitlines(True),now.decode().splitlines(True),
                fromfile='a/'+name,tofile='b/'+name))
(DEST/'native-ui.patch').write_text(''.join(patch))
(DEST/'files.json').write_text(json.dumps(files,indent=2)+'\n')
shutil.copytree(WORK/'baseline',DEST/'baseline',dirs_exist_ok=True)
shutil.copytree(WORK/'reference',DEST/'reference',dirs_exist_ok=True)
local=Path(__file__).parent
for name in ('apply_modern_ui.py','finish_modern_ui.py','build_modern_ui.sh','export_modern_ui.py','verify_modern_ui_image.py'):
    shutil.copy2(local/name,DEST/name)
(DEST/'apply.py').write_text('''"""Apply only onto the recorded working14.1 baseline; fail before any write on mismatch."""
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
''')
print('Exported',len(files),'files, before/after hashes, bring-up baseline, patch and upstream provenance.')
