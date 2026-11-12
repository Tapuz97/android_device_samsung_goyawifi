from pathlib import Path
root=Path('/root/t110-build/lineage20')
def excerpt(rel, words, before=2, after=4):
 p=root/rel;lines=p.read_text().splitlines();print('FILE',rel)
 shown=set()
 for i,s in enumerate(lines):
  if any(w in s for w in words):
   for j in range(max(0,i-before),min(len(lines),i+after)):
    if j not in shown: print(f'{j+1}: {lines[j]}');shown.add(j)
excerpt('frameworks/base/core/jni/AndroidRuntime.cpp',['dalvik.vm.usejit'])
excerpt('art/runtime/jit/jit_memory_region.cc',['memfd_create','Initialize','rwx_memory_allowed_'],2,7)
excerpt('hardware/interfaces/graphics/composer/2.1/utils/passthrough/Android.bp',['shared_libs','libbase','libdl','srcs'],2,7)
excerpt('frameworks/native/libs/ui/include/ui/GraphicBuffer.h',['getStride'],2,3)
