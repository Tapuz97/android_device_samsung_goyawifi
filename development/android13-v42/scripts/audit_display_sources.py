from pathlib import Path
root=Path('/root/t110-build/lineage20')
for rel,words in [
 ('hardware/libhardware/modules/gralloc/framebuffer.cpp',['fb_post','fb_device_open','memcpy','format =']),
 ('hardware/libhardware/modules/gralloc/gralloc.cpp',['ashmem','gralloc_alloc_buffer']),
 ('external/swiftshader/Android.bp',['name:','enabled:','arch:']),
 ('frameworks/native/libs/ui/GraphicBuffer.cpp',['flatten','buf[','stride =']),
 ('frameworks/native/services/surfaceflinger/Layer.cpp',['mActiveBufferStride'])]:
 p=root/rel
 print('FILE',rel)
 if not p.exists(): print('MISSING');continue
 lines=p.read_text().splitlines()
 for i,s in enumerate(lines):
  if any(w in s for w in words):
   a=max(0,i-2);b=min(len(lines),i+6)
   print('\n'.join(f'{j+1}: {lines[j]}' for j in range(a,b)))
