"""Apply the measured SG/VMA mapping fix while preserving the working kernel setup."""
from pathlib import Path
import difflib,hashlib,json,subprocess,sys
p=Path(sys.argv[1]);src=Path('/root/t110-build/kernel-display-i2c');f=src/'drivers/gpu/ion/ion_system_heap.c'
before=f.read_text();start=before.index('int ion_system_heap_map_user(');end=before.index('\nstatic struct ion_heap_ops system_heap_ops',start)
old=before[start:end]
new='''int ion_system_heap_map_user(struct ion_heap *heap, struct ion_buffer *buffer,
\t\t\t     struct vm_area_struct *vma)
{
\tstruct sg_table *table = buffer->priv_virt;
\tunsigned long addr = vma->vm_start;
\tunsigned long offset;
\tstruct scatterlist *sg;
\tint i, ret;

\t/* vm_pgoff counts pages, while an SG entry can span many pages. */
\tif (vma->vm_end <= addr ||
\t    vma->vm_pgoff > (buffer->size >> PAGE_SHIFT))
\t\treturn -EINVAL;
\toffset = vma->vm_pgoff << PAGE_SHIFT;
\tif (vma->vm_end - addr > buffer->size - offset)
\t\treturn -EINVAL;

\tfor_each_sg(table->sgl, sg, table->nents, i) {
\t\tstruct page *page = sg_page(sg);
\t\tunsigned long len = sg_dma_len(sg);

\t\tif (offset >= len) {
\t\t\toffset -= len;
\t\t\tcontinue;
\t\t}
\t\tpage += offset >> PAGE_SHIFT;
\t\tlen -= offset;
\t\toffset = 0;
\t\t/* Never map beyond this VMA, even for a high-order SG entry. */
\t\tlen = min(len, vma->vm_end - addr);
\t\tret = remap_pfn_range(vma, addr, page_to_pfn(page), len,
\t\t\t\t      vma->vm_page_prot);
\t\tif (ret)
\t\t\treturn ret;
\t\taddr += len;
\t\tif (addr == vma->vm_end)
\t\t\treturn 0;
\t}
\treturn -EINVAL;
}
'''
patch=p/'patches/0081-kernel-goya-bound-ion-user-mappings.patch';e=p/'evidence/offline-v41'
if old==new:
    r=json.loads((e/'ion-mapping-source.json').read_text());assert hashlib.sha256(f.read_bytes()).hexdigest()==r['after_sha256'];print('ION_MAPPING_BOUNDS_ALREADY_APPLIED');raise SystemExit(0)
assert 'offset--;' in old and 'addr += sg_dma_len(sg);' in old and 'ret = remap_pfn_range' not in old
after=before[:start]+new+before[end:]
diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/drivers/gpu/ion/ion_system_heap.c',tofile='b/drivers/gpu/ion/ion_system_heap.c'))
if patch.exists():assert patch.read_text()==diff
else:patch.write_text(diff)
subprocess.run(['patch','--dry-run','-p1'],cwd=src,input=diff,text=True,check=True)
subprocess.run(['patch','-p1'],cwd=src,input=diff,text=True,check=True)
assert f.read_text()==after
(e/'ion-mapping-before.c').write_text(old);(e/'ion-mapping-after.c').write_text(new)
record={'source':str(f),'before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':hashlib.sha256(after.encode()).hexdigest(),'fault_source':'recovery-after-codec/SYSTEM_LAST_KMSG@1794332530654.txt.decoded.txt','fault_uptime_seconds':377.417449,'kernel_bug':'mm/memory.c:2202 remap_pfn_range via ion_system_heap_map_user','upstream_basis':'https://android.googlesource.com/kernel/common/+/5023febc3a090aa8c812f6149dca451432f69067/drivers/staging/android/ion/ion_heap.c','status':'SOURCE_APPLIED_NOT_HARDWARE_TESTED'}
(e/'ion-mapping-source.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
