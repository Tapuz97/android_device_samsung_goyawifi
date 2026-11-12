from pathlib import Path
import difflib,hashlib,json,os,subprocess,tempfile
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/hardware-bt-sd';rpath=e/'lookup-watchdog-source.json';record=json.loads(rpath.read_text());root=Path('/root/t110-build/lineage20/packages/modules/Bluetooth');f=root/record['file'];current=f.read_text();sha=lambda data:hashlib.sha256(data).hexdigest();assert sha(current.encode())==record['after_sha256']
patch=p/'patches/0105-bluetooth-ignore-completed-service-lookup-watchdog.patch'
with tempfile.TemporaryDirectory(prefix='bt-watchdog-before-',dir='/root/t110-build') as temporary:
 temp=Path(temporary);old=temp/record['file'];old.parent.mkdir(parents=True);old.write_text(current)
 subprocess.run(['patch','-R','-p1','-i',str(patch)],cwd=temp,capture_output=True,check=True);before=old.read_text();assert sha(before.encode())==record['before_sha256']
after=current.replace('BindOnce([lookup_pending] {','BindOnce([](std::shared_ptr<std::atomic<bool>> lookup_pending) {')
old='        }),\n        std::chrono::milliseconds(500));';new='        }, lookup_pending),\n        std::chrono::milliseconds(500));';assert after.count(old)==1;after=after.replace(old,new)
prefix='#include <atomic>\n#include <memory>\n';assert after.startswith(prefix);after=after[len(prefix):];index=after.index('#include');after=after[:index]+prefix+after[index:]
f.write_text(after);patch.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),'a/'+record['file'],'b/'+record['file'])))
start=after.index('BindOnce([](std::shared_ptr<std::atomic<bool>> lookup_pending)');end=after.index('}, lookup_pending)',start)+1;guard=after[start+len('BindOnce('):end]
work=Path('/root/t110-build/bt-lookup-watchdog-test');cpp=(work/'after.cpp').read_text();begin=cpp.index(' auto timeout=');end=cpp.index(';\n lookup_pending->store',begin)+1
cpp='#include <functional>\n'+cpp[:begin]+' auto timeout=std::bind('+guard+',lookup_pending);'+cpp[end:]
(work/'after.cpp').write_text(cpp);subprocess.run(['g++','-std=c++17','-O2','-pthread',str(work/'after.cpp'),'-o',str(work/'after')],check=True)
result=subprocess.run([str(work/'after')],capture_output=True,timeout=20);assert result.returncode==0
record.update(after_sha256=sha(after.encode()),patch_sha256=sha(patch.read_bytes()),typed_bind_argument=True,failed_native_build_log=(e/'lookup-build-log.txt').read_text().strip());rpath.write_text(json.dumps(record,indent=2)+'\n')
print('CHROMIUM_TYPED_CALLBACK_BINDING_AND_ACTUAL_GUARD_TEST_PASS')
