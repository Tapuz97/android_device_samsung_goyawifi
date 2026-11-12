from pathlib import Path
import difflib,json,hashlib,runpy
root=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');base=Path('/root/t110-build')
a=base/'kernel-binder';b=base/'kernel-binder-modern';rel=Path('drivers/staging/android')
files=[rel/f for f in ['Kconfig','Makefile','binder.c','binder.h','binder_trace.h','binder_compat34.h','uapi/binder.h']]
lines=[]
for f in files:
 before=(a/f).read_text() if (a/f).exists() else '';after=(b/f).read_text()
 lines.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+str(f) if (a/f).exists() else '/dev/null',tofile='b/'+str(f)))
patch=root/'patches/0008-binder-contexts-scatter-gather-backport.patch';patch.write_text(''.join(lines))
# Simulate the preparation script's writes in memory and compare with the built source.
original_read_bytes=Path.read_bytes;original_read_text=Path.read_text;original_write_text=Path.write_text;original_write_bytes=Path.write_bytes;virtual={}
def read_bytes(p):return virtual[p] if p in virtual else original_read_bytes(p)
def read_text(p,*a,**kw):return virtual[p].decode(kw.get('encoding') or 'utf-8') if p in virtual else original_read_text(p,*a,**kw)
def write_bytes(p,data):virtual[p]=data;return len(data)
def write_text(p,data,*a,**kw):virtual[p]=data.encode(kw.get('encoding') or 'utf-8');return len(data)
Path.read_bytes=read_bytes;Path.read_text=read_text;Path.write_bytes=write_bytes;Path.write_text=write_text
try:runpy.run_path(str(root/'scripts/prepare_modern_binder.py'),run_name='__main__')
finally:Path.read_bytes=original_read_bytes;Path.read_text=original_read_text;Path.write_bytes=original_write_bytes;Path.write_text=original_write_text
mismatch=[str(p) for p,data in virtual.items() if p.read_bytes()!=data]
assert not mismatch,mismatch
report={'status':'PASS','preparation_script_reproduces_source':True,'files':{str(f):hashlib.sha256((b/f).read_bytes()).hexdigest() for f in files},'patch_sha256':hashlib.sha256(patch.read_bytes()).hexdigest()}
(root/'evidence/binder-modern-source-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('Exported patch and verified exact preparation of',len(files),'source files')