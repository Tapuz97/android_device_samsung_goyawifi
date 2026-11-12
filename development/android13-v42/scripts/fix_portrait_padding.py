from pathlib import Path
import difflib,re,subprocess,json
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');t=Path('/root/t110-build/lineage20');h=t/'hardware/interfaces';e=p/'evidence/offline-v31';e.mkdir(exist_ok=True)
fb=h/'graphics/composer/2.1/default/T110Framebuffer.cpp';scan=h/'graphics/composer/2.1/default/T110Scanout.h'
text=fb.read_text();(e/'T110Framebuffer.cpp.before').write_text(text)
old='''    if (words[5] != 0x03141592 || !(words[6] & 2) || (words[6] & 1) ||
        !(words[29] & 0x80000000u) || (words[12] != 1 && words[12] != 2) ||
        words[13] != t110::kLogicalWidth || words[14] != t110::kLogicalHeight ||
        words[16] < t110::kLogicalWidth || words[17] < t110::kLogicalHeight ||
        uint64_t(words[16]) * 4 * t110::kLogicalHeight > words[7]) return fail(-EINVAL);'''
assert text.count(old)==1;text=text.replace(old,'    if (!t110::validPortraitAllocation(words)) return fail(-EINVAL);');fb.write_text(text)
text=scan.read_text();(e/'T110Scanout.h.before').write_text(text)
needle='constexpr uint32_t kLogicalHeight = 1024;'
code='''
// Called only after validating native_handle's version, FD and integer counts.
// These legacy fields hold PADDED allocation dimensions (608 for width600),
// not the logical GraphicBuffer dimensions advertised to Android.
inline bool validPortraitAllocation(const uint32_t* words) {
    return words && words[5] == 0x03141592 && (words[6] & 2) && !(words[6] & 1) &&
           (words[29] & 0x80000000u) && (words[12] == 1 || words[12] == 2) &&
           words[13] >= kLogicalWidth && words[14] >= kLogicalHeight &&
           words[16] >= kLogicalWidth && words[17] >= kLogicalHeight &&
           uint64_t(words[16]) * 4 * kLogicalHeight <= words[7];
}
'''
assert needle in text and 'validPortraitAllocation' not in text;scan.write_text(text.replace(needle,needle+code))
for file in [fb,scan]:(p/'work'/file.name).write_text(file.read_text())
paths=['graphics/composer/2.1/default/Android.bp','graphics/composer/2.1/default/service.cpp','graphics/composer/2.1/default/T110Framebuffer.cpp','graphics/composer/2.1/default/T110Framebuffer.h','graphics/composer/2.1/default/T110Scanout.h','graphics/composer/2.1/utils/hwc2onfbadapter/HWC2OnFbAdapter.cpp','graphics/composer/2.1/utils/hwc2onfbadapter/include/hwc2onfbadapter/HWC2OnFbAdapter.h']
patch=''
for name in paths:
    r=subprocess.run(['git','show','HEAD:'+name],cwd=h,capture_output=True,text=True);before=r.stdout if r.returncode==0 else '';after=(h/name).read_text()
    if before==after:continue
    patch+=f'diff --git a/{name} b/{name}\n'+('new file mode 100644\n' if not before else '')
    patch+=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name if before else '/dev/null',tofile='b/'+name))
name='0056-composer-t110-padded-portrait-scanout.patch';(p/'patches'/name).write_text(patch)
subprocess.run(['git','apply','--reverse','--check',str(p/'patches'/name)],cwd=h,check=True)
build=p/'scripts/build_system_image.sh';text=build.read_text();assert '0055-composer-t110-natural-portrait-scanout.patch' in text;build.write_text(text.replace('0055-composer-t110-natural-portrait-scanout.patch',name))
# Use captured allocation fields, not inferred or synthetic dimensions.
capture=(p/'hardware-tests/20261107-145659-core/portrait-output-roundtrip.txt').read_text()
line=next(x for x in capture.splitlines() if x.startswith('OUTPUT logical=600x1024'))
fields={int(k):int(v,16) for k,v in re.findall(r'(\d+):([0-9a-f]+)',line)}
assert fields[13]==fields[16]==608 and fields[14]==fields[17]==1024
fixture=[12,2,34,0,0]+[fields.get(i,0) for i in range(5,39)]
code='#include "'+str(p/'work/T110Scanout.h')+'"\n#include <cassert>\n#include <cstdio>\nint main(){uint32_t words[39]={'+','.join(map(str,fixture))+'};\n'
code+='assert(t110::validPortraitAllocation(words)); assert(!t110::validPortraitAllocation(nullptr));\n'
for field,value in [(5,0),(6,0),(6,3),(29,0),(12,3),(13,599),(14,1023),(16,599),(17,1023),(7,608*4*1024-1)]:
    code+=f'{{auto saved=words[{field}];words[{field}]={value};assert(!t110::validPortraitAllocation(words));words[{field}]=saved;}}\n'
code+='puts("CAPTURED_PADDED_ALLOCATION_AND_REJECTION_PASS");}\n'
scratch=Path('/root/t110-build/portrait-roundtrip');(scratch/'allocation-test.cpp').write_text(code)
subprocess.run(['g++','-std=c++17','-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',str(scratch/'allocation-test.cpp'),'-o',str(scratch/'allocation-test')],check=True)
r=subprocess.run([str(scratch/'allocation-test')],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr;(e/'allocation-regression.log').write_text(r.stdout+r.stderr)
# Run the unchanged full-pixel mapping checks against the updated production header.
subprocess.run(['g++','-std=c++17','-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',str(p/'scripts/test_portrait_scanout.cpp'),'-o',str(scratch/'scanout-test')],check=True)
r2=subprocess.run([str(scratch/'scanout-test')],capture_output=True,text=True);assert r2.returncode==0,r2.stdout+r2.stderr;(e/'scanout-regression.log').write_text(r2.stdout+r2.stderr)
(e/'regressions.json').write_text(json.dumps(dict(status='PASS',real_buffer_fixture=fields,allocation_validation='Captured padded608x1024 accepted; invalid geometry, format, flags, size rejected',scanout='Full-pixel mapping and bounds with ASan/UBSan',android_boots=0),indent=2)+'\n')
print(r.stdout+r2.stdout)
