"""Compile the actual pre-fork function before/after the fix against a lock contract.

This is a host contract regression, NOT an ART/ARM runtime or device boot test.
It forces the checkpoint wait that a fast single-threaded run can skip.
"""
from pathlib import Path
import subprocess, tempfile, json

project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
repo=Path('/root/t110-build/lineage20/art')
current=(repo/'runtime/runtime.cc').read_text()
original=subprocess.check_output(['git','show','HEAD:runtime/runtime.cc'],cwd=repo,text=True)
def function(text):
    start=text.index('void Runtime::PreZygoteFork() {')
    end=text.index('\nvoid Runtime::PostZygoteFork()',start)
    return text[start:end]

prefix=r'''
#include <cassert>
#include <atomic>
#include <condition_variable>
#include <iostream>
#include <mutex>
#include <shared_mutex>
#include <stdexcept>
#include <thread>
#include <vector>
std::shared_mutex mutator;
thread_local bool holding = false;
int checkpoints=0, visits=0, heaps=0, bridges=0, jits=0;
struct Thread { static Thread* Current() { static Thread t; return &t; } };
enum class ThreadState { kWaitingForCheckPointsToRun };
struct ScopedObjectAccess {
  explicit ScopedObjectAccess(Thread*) { assert(!holding); mutator.lock_shared(); holding=true; }
  ~ScopedObjectAccess() { holding=false; mutator.unlock_shared(); }
  Thread* Self() { return Thread::Current(); }
};
struct ScopedThreadStateChange {
  bool was_holding;
  ScopedThreadStateChange(Thread*,ThreadState) : was_holding(holding) {
    if (was_holding) { holding=false; mutator.unlock_shared(); }
  }
  ~ScopedThreadStateChange() {
    if(was_holding) { mutator.lock_shared(); holding=true; }
  }
};
struct FindNativeMethodsVisitor {
  template<class C> FindNativeMethodsVisitor(Thread*, C*) { assert(holding); }
};
struct ClassLinker {
  void MakeInitializedClassesVisiblyInitialized(Thread*,bool wait) {
    assert(wait);
    // The real Barrier::Increment uses ConditionVariable::Wait, which rejects
    // this lock. Force its slow path rather than letting an early pass hide it.
    if(holding) throw std::runtime_error("mutator lock held during checkpoint wait");
    std::mutex lock;
    std::condition_variable condition;
    bool done=false;
    std::unique_lock<std::mutex> guard(lock);
    std::thread worker([&] {
      // GC must be able to acquire the mutator lock while the caller waits.
      std::unique_lock<std::shared_mutex> gc(mutator);
      std::lock_guard<std::mutex> g(lock);
      ++checkpoints;
      done=true;
      condition.notify_one();
    });
    condition.wait(guard,[&] { return done; });
    guard.unlock();
    worker.join();
  }
  void VisitClasses(FindNativeMethodsVisitor*) { assert(holding); ++visits; }
};
struct Heap {
  bool existing=false;
  bool HasZygoteSpace() { return existing; }
  void PreZygoteFork() { assert(!holding); ++heaps; }
};
struct Jit { void PreZygoteFork() { assert(!holding); ++jits; } };
void PreZygoteForkNativeBridge() { assert(!holding); ++bridges; }
struct Runtime {
  Heap heap;
  ClassLinker linker;
  Jit jit;
  bool use_jit=false;
  Heap* heap_=&heap;
  ClassLinker* class_linker_=&linker;
  Jit* GetJit() { return use_jit ? &jit : nullptr; }
  void PreZygoteFork();
};
'''
suffix=r'''
int main() {
  try {
    Runtime runtime;
    for (int i=0;i!=100;++i) {
      runtime.use_jit=(i%2)==0;
      runtime.heap.existing=false;
      runtime.PreZygoteFork();
      runtime.heap.existing=true;
      runtime.PreZygoteFork();
    }
    assert(checkpoints==100 && visits==100 && heaps==200 && bridges==200 && jits==100);
    assert(!holding);
    std::cout << "PASS: 100 forced checkpoint waits and 100 later forks; JNI visits retain mutator access\n";
  } catch (const std::runtime_error& e) {
    std::cout << "REPRODUCED: " << e.what() << '\n';
    return 42;
  }
}
'''
results={}
with tempfile.TemporaryDirectory(prefix='t110-zygote-contract-') as tmp:
    tmp=Path(tmp)
    for label,source in [('baseline',original),('corrected',current)]:
        cpp=tmp/(label+'.cc'); exe=tmp/label
        cpp.write_text(prefix+function(source)+suffix)
        subprocess.run(['g++','-std=c++17','-O1','-Wall','-Wextra','-Werror',
                        '-pthread','-fsanitize=address,undefined',str(cpp),'-o',str(exe)],check=True)
        run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30)
        assert run.returncode == (42 if label=='baseline' else 0),run.stderr+run.stdout
        results[label]={'exit':run.returncode,'stdout':run.stdout,'stderr':run.stderr}
report={'status':'PASS','scope':'Actual source function with host lock-contract doubles; not ART runtime validation',
        'results':results,'hardware_access':False}
out=project/'evidence/offline-v23/zygote-lock-contract.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
