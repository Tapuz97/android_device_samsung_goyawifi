"""Audit each preserved ELF against its own installed DT_NEEDED dependency closure."""
from pathlib import Path
from functools import lru_cache
import json,re,subprocess,sys,hashlib
BASE=Path('/root/t110-lineage14')
SYSTEM=BASE/'android/out/target/product/goyawifi/system'
INPUTS=BASE/'android/device/samsung/goyawifi/vendor-inputs.json'
STAGED='--staged' in sys.argv
entries=json.loads(INPUTS.read_text())['files']
board=(BASE/'android/device/samsung/goyawifi/BoardConfig.mk').read_text()
shim='/system/vendor/lib/libacm.so|libcrypto.so'
assert 'LINKER_FORCED_SHIM_LIBS += '+shim in board
if not STAGED:
    assert shim.encode() in (SYSTEM/'bin/linker').read_bytes(), 'Built linker lacks libacm dependency'
staged={Path(x['destination']).name:Path(x['stock_source']) for x in entries if x['destination'].endswith('.so')}
@lru_cache(None)
def elf(path):
    data=subprocess.run(['readelf','-W','--dyn-syms','-d',str(path)],capture_output=True,text=True,check=True).stdout
    needed=re.findall(r'\(NEEDED\).*?\[(.*?)\]',data)
    defined=set();undefined=set()
    for line in data.splitlines():
        fields=line.split()
        if len(fields)<8 or not fields[0].rstrip(':').isdigit():continue
        _,_,_,typ,bind,vis,index,name=fields[:8]
        name=name.split('@')[0]
        if index=='UND':
            if bind!='WEAK':undefined.add(name)
        elif bind in ('GLOBAL','WEAK') and vis in ('DEFAULT','PROTECTED'):defined.add(name)
    return needed,defined,undefined

def locate(name):
    for parent in ('lib','vendor/lib','vendor/lib/egl'):
        p=SYSTEM/parent/name
        if p.is_file():return p.resolve()
    if STAGED:
        if name in staged:return staged[name]
        p=BASE/'android/out/target/product/goyawifi/obj/SHARED_LIBRARIES'/(name[:-3]+'_intermediates')/'LINKED'/name
        if p.is_file():return p
    return None

results=[]
file_errors=[]
if not STAGED:
    for item in entries:
        p=SYSTEM/Path(item['destination']).relative_to('/system')
        if not p.is_file():file_errors.append({'path':item['destination'],'error':'NOT_INSTALLED'})
        elif hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
            file_errors.append({'path':item['destination'],'error':'HASH_MISMATCH'})
    for name in ('libEGL_MRVL.so','libGLESv1_CM_MRVL.so','libGLESv2_MRVL.so'):
        link=SYSTEM/'vendor/lib'/name
        if not link.is_symlink() or link.resolve()!=(SYSTEM/'vendor/lib/egl'/name).resolve():
            file_errors.append({'path':str(link.relative_to(SYSTEM)),'error':'CANONICAL_DRIVER_SYMLINK_MISSING'})
    for name in ('libEGL.so','libGLES_trace.so','libicuuc.so','libxml2.so','libsync.so'):
        if (SYSTEM/'vendor/lib'/name).exists():
            file_errors.append({'path':'vendor/lib/'+name,'error':'OBSOLETE_PLATFORM_SHADOW'})
for item in entries:
    path=SYSTEM/Path(item['destination']).relative_to('/system')
    with Path(item['stock_source']).open('rb') as f: magic=f.read(4)
    if magic!=b'\x7fELF' or not item['destination'].endswith('.so'):continue
    label=str(path.relative_to(SYSTEM))
    if not path.is_file() and STAGED:path=Path(item['stock_source'])
    if not path.is_file():
        results.append({'path':label,'missing_libraries':['FILE_NOT_INSTALLED'],'missing_symbols':[],'closure_count':0})
        continue
    seen=set();missing=set();available=set()
    def visit(p):
        if p in seen:return
        seen.add(p)
        needed,defined,_=elf(p);available.update(defined)
        if p == (SYSTEM/'vendor/lib/libacm.so').resolve():
            needed=needed+['libcrypto.so']
        for name in needed:
            dep=locate(name)
            if dep:visit(dep)
            else:missing.add(name)
    visit(path.resolve())
    imports=elf(path.resolve())[2]
    results.append({'path':label,'missing_libraries':sorted(missing),
                    'missing_symbols':sorted(imports-available),'closure_count':len(seen)})
report={'status':'PASS' if results and not file_errors and all(not x['missing_libraries'] and not x['missing_symbols'] for x in results) else 'UNRESOLVED',
        'uses_staged_files':STAGED,'file_errors':file_errors,'scope':'Selected original vendor ELFs against per-file installed DT_NEEDED closure plus verified exact-path libacm linker dependency; no runtime execution claim',
        'files':results}
(BASE/'records'/('vendor-elf-precheck.json' if STAGED else 'vendor-elf-verification.json')).write_text(json.dumps(report,indent=2)+'\n')
for error in file_errors:print(json.dumps(error))
for item in results:
    if item['missing_libraries'] or item['missing_symbols']:print(json.dumps(item))
print('Audited',len(results),'vendor ELFs:',report['status'])
