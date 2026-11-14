from pathlib import Path
import subprocess,re
r=Path('/root/t110-android13');s=(r/'android/bionic/linker/linker.cpp').read_text()
start=s.index('    const bool t110_gpu =')
end=s.index('      DL_ERR_AND_LOG',start)
code=s[start:end]
code=code.replace('    if (app_target_api_level >= 23 && !t110_gpu && !t110_audio) {','    return app_target_api_level >= 23 && !t110_gpu && !t110_audio;')
assert 'return app_target_api_level' in code
test='''#include <cassert>
#include <cstring>
#include <cstdio>
bool gpu=false,audio=false;const char* path;
namespace android { namespace base { bool GetBoolProperty(const char* key,bool){return !strcmp(key,"ro.t110.legacy_gpu")?gpu:audio;} } }
const char* get_realpath(){return path;}
bool denied(int app_target_api_level){
'''+code+'''}
int main(){
path="/vendor/lib/libippsp.so";assert(denied(33));audio=true;assert(!denied(33));
path="/system/vendor/lib/libippsp.so";assert(!denied(33));
path="/data/local/tmp/libippsp.so";assert(denied(33));
path="/vendor/lib/libippsp.so.backup";assert(denied(33));
path="/vendor/lib/other.so";assert(denied(33));
path="/vendor/lib/libGAL.so";assert(denied(33));gpu=true;assert(!denied(33));
audio=false;path="/vendor/lib/libippsp.so";assert(denied(33));
gpu=false;path="/vendor/lib/other.so";assert(!denied(22));
puts("PASS: actual linker predicates retain opt-in/exact-path/device separation and normal target-SDK checks");
}
'''
p=r/'textrel-scope-test.cpp';p.write_text(test)
binary=r/'textrel-scope-test'
subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(p),'-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
