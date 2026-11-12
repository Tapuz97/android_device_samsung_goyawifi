"""Cancel the lookup watchdog logically before tearing down its timer."""
from pathlib import Path
import difflib,hashlib,json,os,resource,subprocess
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/hardware-bt-sd';root=Path('/root/t110-build/lineage20/packages/modules/Bluetooth');name='system/gd/hal/hci_hal_android_hidl.cc';f=root/name;receipt=e/'lookup-watchdog-source.json'
sha=lambda data:hashlib.sha256(data).hexdigest()
if receipt.exists():assert sha(f.read_bytes())==json.loads(receipt.read_text())['after_sha256'];print('LOOKUP_WATCHDOG_ALREADY_FIXED');raise SystemExit(0)
before=f.read_text();old='''    auto get_service_alarm = new os::Alarm(GetHandler());
    get_service_alarm->Schedule(
        BindOnce([] {
          LOG_ALWAYS_FATAL("Unable to get a Bluetooth service after 500ms, start the HAL before starting Bluetooth");
        }),
        std::chrono::milliseconds(500));''';assert before.count(old)==1
guard='''[](std::shared_ptr<std::atomic<bool>> lookup_pending) {
          if (lookup_pending->exchange(false, std::memory_order_acq_rel)) {
            LOG_ALWAYS_FATAL("Unable to get a Bluetooth service after 500ms, start the HAL before starting Bluetooth");
          }
        }'''
new='''    auto lookup_pending = std::make_shared<std::atomic<bool>>(true);
    auto get_service_alarm = new os::Alarm(GetHandler());
    get_service_alarm->Schedule(
        BindOnce('''+guard+''', lookup_pending),
        std::chrono::milliseconds(500));'''
after=before.replace(old,new);marker='    get_service_alarm->Cancel();';assert after.count(marker)==1
after=after.replace(marker,'''    // A timer callback can already be runnable when lookup finishes. Once
    // the service has been obtained, that stale timeout must not abort startup.
    lookup_pending->store(false, std::memory_order_release);
'''+marker)
index=after.index('#include');after=after[:index]+'#include <atomic>\n#include <memory>\n'+after[index:]
patch=p/'patches/0105-bluetooth-ignore-completed-service-lookup-watchdog.patch';assert not patch.exists();patch.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),'a/'+name,'b/'+name)));f.write_text(after)
work=Path('/root/t110-build/bt-lookup-watchdog-test');work.mkdir(exist_ok=True)
test='''#include <atomic>
#include <cassert>
#include <functional>
#include <memory>
#include <thread>
static std::atomic<int> fatal_count{0};
#define LOG_ALWAYS_FATAL(...) (++fatal_count)
int main() {
 auto lookup_pending=std::make_shared<std::atomic<bool>>(true);
 auto timeout=std::bind(GUARD,lookup_pending);
 lookup_pending->store(false,std::memory_order_release);
 std::thread delayed([&]{ timeout(); });delayed.join();
 assert(fatal_count.load()==0); // Already-completed lookup, late runnable timer.
 lookup_pending->store(true);timeout();assert(fatal_count.load()==1);
 timeout();assert(fatal_count.load()==1); // Pending timeout remains fatal once.
 for(int i=0;i<1000;++i) {
  lookup_pending->store(true);int before=fatal_count.load();
  std::thread cancel([&]{lookup_pending->store(false,std::memory_order_release);});
  std::thread fire([&]{timeout();});cancel.join();fire.join();
  assert(fatal_count.load()==before || fatal_count.load()==before+1);
 }
}
'''
results={}
for label,body in [('before','[](std::shared_ptr<std::atomic<bool>>) { LOG_ALWAYS_FATAL("old watchdog"); }'),('after',guard)]:
 src=work/(label+'.cpp');src.write_text(test.replace('GUARD',body));exe=work/label
 subprocess.run(['g++','-std=c++17','-O2','-pthread',str(src),'-o',str(exe)],check=True)
 result=subprocess.run([str(exe)],capture_output=True,timeout=20,preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_CORE,(0,0)));results[label]=result.returncode
assert results['before']!=0 and results['after']==0,results
record=dict(file=name,before_sha256=sha(before.encode()),after_sha256=sha(after.encode()),patch_sha256=sha(patch.read_bytes()),
 watchdog_milliseconds_unchanged=500,actual_guard_lambda_test=results,race_trials=1000,missing_service_still_fatal=True,
 evidence='After getService returned and HAL initialized firmware, the old lookup alarm still aborted the app. Mode-fix live evidence retained.',status='SOURCE_TESTED_NOT_ROM_BUILT')
receipt.write_text(json.dumps(record,indent=2)+'\n');print('LOOKUP_WATCHDOG_ACTUAL_GUARD_TEST_BEFORE_FAIL_AFTER_PASS',results)
