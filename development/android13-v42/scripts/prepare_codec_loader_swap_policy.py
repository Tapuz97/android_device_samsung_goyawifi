"""Narrow APEX library lookup and retain the old kernel's explicit swap permission."""
from pathlib import Path
import difflib,hashlib,json,sys
p=Path(sys.argv[1]);t=Path(sys.argv[2]);e=p/'evidence/offline-v41'
changes=[('frameworks/native','libs/ui/Gralloc2.cpp','0082-gralloc-t110-isolated-apex-hardware-lookup.patch',
'''        void* library = dlopen("libhardware.so", RTLD_NOW | RTLD_LOCAL);
''','''        void* library = dlopen("libhardware.so", RTLD_NOW | RTLD_LOCAL);
        if (!library) {
            // The codec APEX permits /system/lib but does not search it for
            // this optional library. Keep its existing namespace isolation.
#if defined(__LP64__)
            library = dlopen("/system/lib64/libhardware.so", RTLD_NOW | RTLD_LOCAL);
#else
            library = dlopen("/system/lib/libhardware.so", RTLD_NOW | RTLD_LOCAL);
#endif
        }
'''),
('system/sepolicy','private/access_vectors','0083-sepolicy-t110-legacy-swap-permission.patch',
'''\twatch_reads
}
''','''\twatch_reads
ifdef(`t110_legacy_swapon', `\tswapon')
}
''')]
records=[]
for repo,rel,patchname,old,new in changes:
    f=t/repo/rel;s=f.read_text()
    if new in s:
        assert s.count(new)==1;records.append({'file':repo+'/'+rel,'status':'ALREADY_APPLIED'});continue
    assert s.count(old)==1,(str(f),s.count(old))
    after=s.replace(old,new);patch=''.join(difflib.unified_diff(s.splitlines(True),after.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
    pf=p/'patches'/patchname
    if pf.exists():assert pf.read_text()==patch
    else:pf.write_text(patch)
    f.write_text(after);records.append({'file':repo+'/'+rel,'before_sha256':hashlib.sha256(s.encode()).hexdigest(),'after_sha256':hashlib.sha256(after.encode()).hexdigest(),'patch':patchname})
(e/('loader-swap-source-'+t.parent.name+'.json')).write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2))
