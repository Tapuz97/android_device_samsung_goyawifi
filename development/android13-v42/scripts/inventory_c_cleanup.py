"""Read-only size inventory. Does not follow junctions or remove user files."""
from pathlib import Path
import os,json,collections,shutil,time
project=Path(__file__).resolve().parents[1]
totals=collections.Counter();large=[];errors=[];start=time.time()
roots=[Path('C:/Users/Gal'),Path('C:/ProgramData'),Path('C:/Windows/Temp')]
for root in roots:
    for base,dirs,files in os.walk(root,followlinks=False,onerror=lambda e:errors.append(str(e))):
        dirs[:]=[d for d in dirs if not os.path.isjunction(Path(base)/d) and not os.path.islink(Path(base)/d)]
        for name in files:
            p=Path(base)/name
            try:
                size=p.stat().st_size
            except OSError:continue
            rel=p.relative_to(root).parts
            group=str(root.joinpath(*rel[:min(3,len(rel)-1)]))
            totals[group]+=size
            if size>512*1024*1024:large.append({'path':str(p),'bytes':size})
    print('SCANNED',str(root),flush=True)
result={'scope':[str(x) for x in roots],'largest_groups':totals.most_common(80),
 'large_files':sorted(large,key=lambda x:-x['bytes']),'free_c_bytes':shutil.disk_usage(project).free,
 'errors':errors,'seconds':time.time()-start,'files_deleted':0}
(project/'cleanup/lineage14-pivot/c-drive-inventory.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'top_groups':totals.most_common(20),'largest_files':result['large_files'][:15],'free_c_bytes':result['free_c_bytes']},indent=2),flush=True)
