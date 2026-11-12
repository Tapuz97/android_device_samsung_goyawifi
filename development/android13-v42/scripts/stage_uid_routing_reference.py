"""Stage UID-related Linux3.4 reference hunks for review; do not change the kernel."""
from pathlib import Path
import difflib,json,re,hashlib

p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
src=Path('/root/t110-build/kernel-display-i2c')
work=Path('/root/t110-build/uid-routing-backport')
refs=p/'evidence/hardware-v35/uid-upstream'
paths=set(re.findall(r'^diff --git a/(\S+)',(refs/'legacy-uid.patch').read_text(),re.M))
paths={f.replace('include/uapi/','include/') for f in paths}
records=[];patch=[]
for name in sorted(paths):
    f=src/name;ref=refs/('hammerhead-'+name.replace('/','_'))
    if not f.is_file() or not ref.is_file():continue
    before=f.read_text();after=ref.read_text()
    old=before.splitlines(True);new=after.splitlines(True)
    groups=list(difflib.SequenceMatcher(None,old,new,autojunk=False).get_grouped_opcodes(3))
    chosen=[]
    for group in groups:
        changed=''.join(''.join(old[a:b])+''.join(new[c:d]) for tag,a,b,c,d in group if tag!='equal')
        if re.search(r'\b(?:uid|rt_uid|flowi[46]?_uid|flowic_uid|uid_start|uid_end|uid_t|kuid_t|FRA_UID_\w+|RTA_UID|INVALID_UID|sock_i_uid)\b',changed):chosen.append(group)
    if not chosen:continue
    base=work/'base'/name;base.parent.mkdir(parents=True,exist_ok=True)
    if base.exists():assert base.read_text()==before,'Source changed since reference staging'
    else:base.write_text(before)
    patch.extend(['--- a/'+name+'\n','+++ b/'+name+'\n'])
    def span(start,end):
        length=end-start
        return str(start+1) if length==1 else str(start if not length else start+1)+','+str(length)
    for group in chosen:
        patch.append('@@ -'+span(group[0][1],group[-1][2])+' +'+span(group[0][3],group[-1][4])+' @@\n')
        for tag,a,b,c,d in group:
            if tag=='equal':patch.extend(' '+line for line in old[a:b])
            else:
                if tag in ('replace','delete'):patch.extend('-'+line for line in old[a:b])
                if tag in ('replace','insert'):patch.extend('+'+line for line in new[c:d])
    records.append(dict(path=name,base_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),hunks=len(chosen)))
work.mkdir(exist_ok=True)
(work/'reference-only.patch').write_text(''.join(patch))
(p/'evidence/hardware-v35/uid-reference-stage.json').write_text(json.dumps(records,indent=2)+'\n')
print('REFERENCE_ONLY',len(records),'files',len(''.join(patch)),'patch bytes')
