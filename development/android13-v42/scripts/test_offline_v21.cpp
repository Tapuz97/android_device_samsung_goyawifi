#include "../work/T110Scanout.h"
#include <cassert>
#include <vector>
#include <cstdio>

int main() {
    fb_fix_screeninfo f{};
    fb_var_screeninfo v{};
    v.xres=v.xres_virtual=1024; v.yres=600; v.yres_virtual=1800;
    v.bits_per_pixel=32; v.red={16,8,0}; v.green={8,8,0};
    v.blue={0,8,0}; v.transp={24,8,0};
    f.type=FB_TYPE_PACKED_PIXELS; f.visual=FB_VISUAL_TRUECOLOR;
    f.line_length=4160; f.smem_len=f.line_length*1800; f.ypanstep=1;
    std::vector<uint8_t> dst(f.smem_len+16,0x5a), src(1056*4*600,0);
    for (unsigned y=0;y<600;++y) for(unsigned x=0;x<1024;++x) {
        auto i=(y*1056+x)*4;
        src[i]=x%256;src[i+1]=y%256;src[i+2]=(x+y)%256;
    }
    assert(t110::copyFrame(dst.data(),f.smem_len,f,v,600,src.data(),src.size(),1056));
    for(unsigned y=0;y<1800;++y) for(unsigned x=0;x<f.line_length;++x) {
        uint8_t expected=0x5a;
        if(y>=600 && y<1200 && x<4096) {
            unsigned pixel=x/4, row=y-600;
            switch(x%4) {
                case 0:expected=(pixel+row)%256;break;
                case 1:expected=row%256;break;
                case 2:expected=pixel%256;break;
                case 3:expected=255;break;
            }
        }
        assert(dst[y*f.line_length+x]==expected);
    }
    for(size_t i=f.smem_len;i<dst.size();++i) assert(dst[i]==0x5a);
    auto before=dst;
    assert(!t110::copyFrame(dst.data(),f.smem_len,f,v,1800,src.data(),src.size(),1056));
    assert(!t110::copyFrame(dst.data(),f.smem_len,f,v,601,src.data(),src.size(),1056));
    assert(!t110::copyFrame(dst.data(),f.smem_len,f,v,600,src.data(),src.size()-1,1056));
    assert(!t110::copyFrame(dst.data(),f.smem_len,f,v,600,src.data(),src.size(),1023));
    assert(!t110::copyFrame(dst.data(),4096,f,v,600,src.data(),src.size(),1056));
    assert(dst==before);
    auto bad=v; bad.green=bad.red; assert(!t110::validFramebuffer(f,bad));
    bad=v;bad.red.offset=31;assert(!t110::validFramebuffer(f,bad));
    bad=v;bad.yres_virtual=600;assert(!t110::validFramebuffer(f,bad));
    bad=v;bad.bits_per_pixel=16;assert(!t110::validFramebuffer(f,bad));
    bad=v;bad.red.msb_right=1;assert(!t110::validFramebuffer(f,bad));
    f.ypanstep=7;assert(!t110::validFramebuffer(f,v));
    puts("PASS: padded RGBA conversion, page isolation, bounds and unsupported geometry");
}
