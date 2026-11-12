"""Compile the extracted real old/new map_user functions against a recording MM shim."""
from pathlib import Path
import json,subprocess,tempfile,sys
p=Path(sys.argv[1]);e=p/'evidence/offline-v41'
old=(e/'ion-mapping-before.c').read_text().replace('ion_system_heap_map_user(', 'old_map_user(')
new=(e/'ion-mapping-after.c').read_text().replace('ion_system_heap_map_user(', 'fixed_map_user(')
prefix=r'''
#include <assert.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#define PAGE_SHIFT 12
#define PAGE_SIZE (1UL << PAGE_SHIFT)
#define min(a,b) ((a)<(b)?(a):(b))
struct page {unsigned long pfn;};
struct scatterlist {struct page *page; unsigned long length;};
struct sg_table {struct scatterlist *sgl; unsigned int nents;};
struct ion_heap {int unused;};
struct ion_buffer {struct sg_table *priv_virt; unsigned long size;};
struct vm_area_struct {unsigned long vm_start,vm_end,vm_pgoff,vm_page_prot;};
#define sg_page(s) ((s)->page)
#define sg_dma_len(s) ((s)->length)
#define page_to_pfn(p) ((p)->pfn)
#define for_each_sg(list,sg,n,i) for((i)=0,(sg)=(list);(i)<(int)(n);++(i),++(sg))
static struct sg_table *expected_table;
static unsigned long expected_offset, mapped;
static int calls, fail_at, overrun;
static unsigned long expected_pfn(unsigned long off) {
    unsigned i;
    for(i=0;i<expected_table->nents;i++) {
        struct scatterlist *sg=&expected_table->sgl[i];
        if(off<sg->length)return sg->page[off/PAGE_SIZE].pfn;
        off-=sg->length;
    }
    return ULONG_MAX;
}
static int remap_pfn_range(struct vm_area_struct *v,unsigned long addr,
        unsigned long pfn,unsigned long bytes,unsigned long prot) {
    unsigned long n;(void)prot;
    ++calls;
    if(addr<v->vm_start || addr>v->vm_end || bytes>v->vm_end-addr) {
        ++overrun;return -EEXIST;
    }
    if(calls==fail_at)return -ENOMEM;
    assert(addr==v->vm_start+mapped && bytes && !(bytes%PAGE_SIZE));
    for(n=0;n<bytes;n+=PAGE_SIZE)
        assert(pfn+n/PAGE_SIZE==expected_pfn(expected_offset+mapped+n));
    mapped+=bytes;return 0;
}
'''
suffix=r'''
static struct page pages[1024];
static struct scatterlist sg[3];
static struct sg_table table={sg,3};
static struct ion_buffer buffer={&table,0};
static void reset(unsigned long offset,int failure) {
    expected_table=&table;expected_offset=offset;mapped=0;calls=0;fail_at=failure;overrun=0;
}
static int check(unsigned long off,unsigned long len,int failure) {
    struct vm_area_struct v={0xb5697000UL,0xb5697000UL+len,off/PAGE_SIZE,0};
    int ret;reset(off,failure);ret=fixed_map_user(NULL,&buffer,&v);
    assert(!overrun);
    if(failure>0)assert(ret==-ENOMEM);
    else {assert(!ret);assert(mapped==len);}
    return calls;
}
int main(void) {
    unsigned long i,total,off,len;unsigned seed=0x110;int cases=0;
    for(i=0;i<1024;i++)pages[i].pfn=0x9000+i;
    sg[0]=(struct scatterlist){pages,256*PAGE_SIZE};
    sg[1]=(struct scatterlist){pages+512,16*PAGE_SIZE};
    sg[2]=(struct scatterlist){pages+900,PAGE_SIZE};
    total=buffer.size=273*PAGE_SIZE;
    /* Actual crash shape: 1MiB SG entry, 4KiB VMA. Old code ignores the MM error. */
    {
        struct vm_area_struct v={0xb5697000UL,0xb5698000UL,0,0};
        reset(0,0);assert(old_map_user(NULL,&buffer,&v)==0);assert(overrun==1);
    }
    assert(check(0,PAGE_SIZE,0)==1);++cases;
    assert(check(8*PAGE_SIZE,2*PAGE_SIZE,0)==1);++cases;
    assert(check(255*PAGE_SIZE,2*PAGE_SIZE,0)==2);++cases;
    assert(check(256*PAGE_SIZE,PAGE_SIZE,0)==1);++cases;
    assert(check(272*PAGE_SIZE,PAGE_SIZE,0)==1);++cases;
    assert(check(0,total,0)==3);++cases;
    check(255*PAGE_SIZE,2*PAGE_SIZE,2);++cases;
    check(0,PAGE_SIZE,1);++cases;
    /* All page-aligned start/length combinations in a mixed-order allocation. */
    for(off=0;off<total;off+=PAGE_SIZE)for(len=PAGE_SIZE;len<=total-off;len+=PAGE_SIZE) {
        check(off,len,0);++cases;
    }
    /* Invalid ranges, including offset overflow, must fail without any MM call. */
    {
        struct vm_area_struct bad[4]={{0x10000,0x11000,274,0},{0x10000,0x12000,272,0},
            {0x10000,0x11000,ULONG_MAX,0},{0x10000,0x10000,0,0}};
        for(i=0;i<4;i++){reset(0,0);assert(fixed_map_user(NULL,&buffer,&bad[i])==-EINVAL);assert(!calls);++cases;}
    }
    /* A truncated SG list is an error, never a falsely successful partial mmap. */
    {
        struct vm_area_struct v={0x10000,0x10000+total,0,0};table.nents=1;
        reset(0,0);assert(fixed_map_user(NULL,&buffer,&v)==-EINVAL);assert(mapped==sg[0].length);++cases;
    }
    (void)seed;
    printf("OLD_OVERRUN_REPRODUCED FIXED_CASES=%d ALL_PASS\n",cases);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='t110-ion-map-') as tmp:
    src=Path(tmp)/'test.c';binary=Path(tmp)/'test';src.write_text(prefix+old+new+suffix)
    subprocess.run(['gcc','-std=gnu99','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-Wall','-Wextra','-Wno-unused-parameter',str(src),'-o',str(binary)],check=True)
    r=subprocess.run([str(binary)],text=True,capture_output=True,check=True)
    (e/'ion-mapping-host-test.txt').write_text(r.stdout+r.stderr)
    report={'status':'PASS','source':'Extracted original and patched production map_user C functions, compiled with ASan/UBSan','negative_control':'Original function requests 1MiB outside4KiB VMA and ignores remap error','positive_cases':'All mixed-order allocation page ranges, intra-SG/nonzero offsets, cross-SG, exact boundaries, MM errors, out-of-range/overflow/empty ranges, short SG table','hardware_decode_passed':False,'output':r.stdout.strip()}
    (e/'ion-mapping-host-test.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
