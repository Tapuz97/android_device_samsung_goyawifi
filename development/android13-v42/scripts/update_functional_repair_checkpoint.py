"""Update the live checklist, preserving the immutable pre-repair baseline."""
from pathlib import Path
from collections import Counter
import json
p=Path(__file__).resolve().parents[1];e=p/'evidence/functional-audit-20261110'
d=json.loads((e/'checklist.json').read_text());baseline=(e/'baseline-before-fixes.json').read_bytes()
for item in d['items']:
    if item['id']=='CORE16':item.update(status='PARTIAL',evidence=['../remote-fixes-20261110/clock-fix.json'],note='Current time and Asia/Jerusalem timezone corrected through AlarmManager; RTC updated and offset below1second. Persistence through reboot and automatic network time still pending.')
    if item['id']=='APP03':item.update(evidence=['settings-query.xml','keyboard-q.xml','search-result-final.xml','search-result-final.png'],note='Native Settings search accepts text, lists Wi-Fi results and opens the real Internet settings page without the prior crash. Broad indexing coverage remains unqualified.')
    if item['id']=='APP04':item.update(evidence=['keyboard-q.xml','settings-query.png','ime.txt'],note='Native LatinIME opens correctly; tapping its q key appended q to the search editor. Owner finger typing and broader keyboard behavior remain in the handoff.')
d['summary']=dict(Counter(i['status'] for i in d['items']));d['repair_progress']='Remote source fixes/builds in evidence/remote-fixes-20261110; only actual installed/retested functions can gain PASS.'
(e/'checklist.json').write_text(json.dumps(d,indent=2)+'\n');assert (e/'baseline-before-fixes.json').read_bytes()==baseline
lines=['# Functional checklist — SM-T110 / LineageOS20','',
'Automatic assessment completed before repairs. Functional development is still in progress.',
'The owner authorized remote fixes while away. Hands-on and accessory checks remain open.',
'UI/performance polish, extra features and HQ wallpaper work wait until functional completion.','',
'Only PASS is ticked. A built patch, listed service or a returned but corrupted image is not a functional pass.',
'Counts: '+', '.join(f'{k}={v}' for k,v in d['summary'].items())+'.','',
'Installed audit baseline: system v27 / BOOT v29.',
'[Repair progress](evidence/remote-fixes-20261110/README.md). [Immutable baseline](evidence/functional-audit-20261110/baseline-before-fixes.json).','']
group=None
for i in d['items']:
    if group!=i['group']:group=i['group'];lines+=['## '+group,'']
    links=', '.join('[evidence](evidence/functional-audit-20261110/'+v+')' for v in i['evidence'])
    lines.append(f'- [{"x" if i["status"]=="PASS" else " "}] **{i["id"]} {i["function"]} — {i["status"]}**. {i["note"]} {links}')
(p/'FUNCTIONAL-CHECKLIST.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(json.dumps(d['summary'],indent=2))
