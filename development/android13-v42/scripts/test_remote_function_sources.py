"""Compile extracted production methods against controlled absent/ready/error HALs."""
from pathlib import Path
import re,json,subprocess,hashlib
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');t=Path('/root/t110-build/lineage20')
e=p/'evidence/remote-fixes-20261110';test=e/'source-tests';test.mkdir(exist_ok=True)
def method(text,signature):
    start=text.index(signature);brace=text.index('{',start);depth=1;end=brace+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]
src=(t/'lineage-sdk/sdk/src/java/lineageos/hardware/LineageHardwareManager.java').read_text()
constants=re.findall(r'public static final int (FEATURE_\w+) = (0x[0-9a-fA-F]+);',src)
hal_method=method(src,'private IBase getHIDLService(int feature)')
hals=re.findall(r'return (\w+)\.getService\(retry\);',hal_method);assert len(hals)==16
java='''import java.util.*;
public class HardwareProbeTest {
static boolean probe=true,available=false,lastRetry; static int hardwareFeatures=0,calls=0;
interface IBase {} static class Ready implements IBase {}
static class RemoteException extends Exception {}
static class SystemProperties {static boolean getBoolean(String key,boolean fallback){if(!key.equals("ro.t110.optional_hal_probe"))throw new AssertionError();return probe;}}
static class HAL {static IBase getService(boolean retry)throws RemoteException {calls++;lastRetry=retry;if(!available)throw new NoSuchElementException();return new Ready();}}
static class Service {int getSupportedFeatures()throws RemoteException{return hardwareFeatures;}}
static Service sService=new Service(); boolean checkService(){return true;}
HashMap<Integer,IBase> mHIDLMap=new HashMap<>();
'''
java+='\n'.join('public static final int '+a+'='+b+';' for a,b in constants)+'\n'
java+='\n'.join('static class '+h+' extends HAL {}' for h in hals)+'\n'+hal_method+'\n'
for sig in ['public boolean isSupported(int feature)','private boolean isSupportedHIDL(int feature)','private boolean isSupportedHWC2(int feature)']:java+=method(src,sig)+'\n'
features=re.findall(r'case (FEATURE_\w+):',hal_method)
java+='''static void require(boolean ok){if(!ok)throw new AssertionError();}
public static void main(String[] args) throws Exception {
int[] features={'''+','.join(features)+'''};
for(boolean legacy:new boolean[]{true,false})for(boolean present:new boolean[]{false,true}) {
probe=legacy;available=present;hardwareFeatures=0;
for(int f:features){HardwareProbeTest m=new HardwareProbeTest();int before=calls;
require(m.isSupported(f)==present);require(calls==before+1);require(lastRetry==!legacy);
require(m.isSupported(f)==present);require(calls==before+1);}
}
probe=true;available=false;hardwareFeatures=FEATURE_KEY_DISABLE;
require(new HardwareProbeTest().isSupported(FEATURE_KEY_DISABLE));
require(!new HardwareProbeTest().isSupported(FEATURE_HIGH_TOUCH_POLLING_RATE));
System.out.println("PASS:16 optional HALs, absent/ready, property on/off, cache and HWC2 fallback");
}}
'''
(test/'HardwareProbeTest.java').write_text(java)
jdk=t/'prebuilts/jdk/jdk11/linux-x86/bin'
subprocess.run([str(jdk/'javac'),'-d',str(test),str(test/'HardwareProbeTest.java')],check=True)
j=subprocess.check_output([str(jdk/'java'),'-cp',str(test),'HardwareProbeTest'],text=True)

native=(t/'frameworks/native/libs/ui/Gralloc2.cpp').read_text()
import_method=method(native,'status_t Gralloc2Mapper::importBuffer(')
cpp='''#include <cassert>
#include <cstdio>
using status_t=int;using buffer_handle_t=const void*;
constexpr int NO_INIT=-19;enum class Error{NONE=0,BAD_BUFFER=2,NO_RESOURCES=5};constexpr Error kTransactionError=Error::NO_RESOURCES;
namespace hardware {struct hidl_handle{};}
struct Result{bool ok;bool isOk(){return ok;}};
static bool enabled=true,ready=true,transport=true;static Error error=Error::NONE;static int imports=0;
struct T110LegacyAllocation {static T110LegacyAllocation& get(){static T110LegacyAllocation state;return state;}bool enabled_()const{return ::enabled;}bool ready_()const{return ::ready;}};
#define enabled enabled_
#define ready ready_
struct Mapper {template<class F>Result importBuffer(const hardware::hidl_handle&,F f){imports++;f(error,reinterpret_cast<void*>(123));return {transport};}};
struct Gralloc2Mapper {Mapper object;Mapper* mMapper=&object;status_t importBuffer(const hardware::hidl_handle&,buffer_handle_t*)const;};
'''+import_method+'''
#undef enabled
#undef ready
int main(){Gralloc2Mapper m;hardware::hidl_handle raw;buffer_handle_t out=nullptr;
enabled=true;ready=false;assert(m.importBuffer(raw,&out)==NO_INIT&&imports==0);
ready=true;assert(m.importBuffer(raw,&out)==0&&imports==1&&out==reinterpret_cast<void*>(123));
enabled=false;ready=false;assert(m.importBuffer(raw,&out)==0&&imports==2);
enabled=true;ready=true;error=Error::BAD_BUFFER;assert(m.importBuffer(raw,&out)==2);
transport=false;assert(m.importBuffer(raw,&out)==5);
puts("PASS:import-only initialization guard, normal imports, disabled device path, mapper/transport errors");}
'''
(test/'import-only-test.cpp').write_text(cpp)
subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(test/'import-only-test.cpp'),'-o',str(test/'import-only-test')],check=True)
c=subprocess.check_output([str(test/'import-only-test')],text=True)
record={'java':j.strip(),'native':c.strip(),'scope':'Extracted production methods with controlled dependencies, not full framework build or hardware validation','source_sha256':{'LineageHardwareManager.java':hashlib.sha256(src.encode()).hexdigest(),'Gralloc2.cpp':hashlib.sha256(native.encode()).hexdigest()}}
(e/'source-tests.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
