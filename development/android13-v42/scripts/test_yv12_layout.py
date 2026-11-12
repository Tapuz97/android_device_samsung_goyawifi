"""Check the exact production layout helper with bounds and overflow controls."""
from pathlib import Path
import json,subprocess,sys,tempfile
p=Path(sys.argv[1]);header=p/'work/device/samsung/t110_bringup/graphics/T110Yv12Layout.h'
code=r'''
#include "T110Yv12Layout.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void) {
    struct t110_yv12_layout s;
    assert(t110_compute_yv12_layout(256,144,256,&s));
    assert(s.y_stride==256 && s.c_stride==128 && s.y_size==36864 && s.c_size==9216 && s.total_size==55296);
    assert(t110_compute_yv12_layout(258,146,272,&s));
    assert(s.y_size==39712 && s.c_stride==144 && s.c_size==10512 && s.total_size==60736);
    unsigned widths[]={2,16,18,256,258,640,1024};
    unsigned heights[]={2,16,144,146,480,600};unsigned n=0;
    for(unsigned w=0;w<7;w++)for(unsigned h=0;h<6;h++)for(unsigned pad=0;pad<3;pad++) {
        unsigned stride=((widths[w]+15)&~15U)+pad*16;
        assert(t110_compute_yv12_layout(widths[w],heights[h],stride,&s));
        assert(s.y_stride>=widths[w] && !(s.y_stride%16));
        assert(s.c_stride>=widths[w]/2 && !(s.c_stride%16));
        assert(s.y_size==s.y_stride*heights[h]);
        assert(s.c_size==s.c_stride*(heights[h]/2));
        unsigned char *data=malloc(s.total_size+16);assert(data);
        memset(data,0x5a,s.total_size+16);memset(data,16,s.y_size);
        memset(data+s.y_size,128,s.c_size);memset(data+s.y_size+s.c_size,192,s.c_size);
        assert(data[s.y_size-1]==16 && data[s.y_size]==128);
        assert(data[s.y_size+s.c_size-1]==128 && data[s.y_size+s.c_size]==192);
        assert(data[s.total_size-1]==192 && data[s.total_size]==0x5a);
        free(data);n++;
    }
    assert(!t110_compute_yv12_layout(0,144,256,&s));
    assert(!t110_compute_yv12_layout(255,144,256,&s));
    assert(!t110_compute_yv12_layout(256,143,256,&s));
    assert(!t110_compute_yv12_layout(256,144,240,&s));
    assert(!t110_compute_yv12_layout(256,144,257,&s));
    assert(!t110_compute_yv12_layout(256,144,256,NULL));
    assert(!t110_compute_yv12_layout(0xffffffd0U,0xfffffffeU,0xfffffff0U,&s));
    printf("YV12_LAYOUT_VALID_RANGE_CASES=%u INVALID_AND_OVERFLOW_CONTROLS_PASS\n",n);
}
'''
with tempfile.TemporaryDirectory(prefix='t110-yv12-layout-') as tmp:
    src=Path(tmp)/'test.c';binary=Path(tmp)/'test';src.write_text(code)
    subprocess.run(['cc','-std=c99','-O1','-g','-fsanitize=address,undefined','-fno-omit-frame-pointer','-Wall','-Wextra','-Werror','-I',str(header.parent),str(src),'-o',str(binary)],check=True)
    r=subprocess.run([str(binary)],text=True,capture_output=True,check=True)
    (p/'evidence/offline-v41/yv12-layout-host-test.json').write_text(json.dumps({'status':'PASS','output':r.stdout.strip(),'sanitizers':'ASan and UBSan','helper':'Exact production header','hardware_codec_passed':False},indent=2)+'\n');print(r.stdout)
