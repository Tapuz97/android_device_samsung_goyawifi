#include "../work/T110Scanout.h"
#include <cassert>
#include <vector>
#include <cstdio>
#include <limits>
int main() {
    for(unsigned stride: {600u,608u,640u}) for(unsigned pitch: {4096u,4224u})
    for(unsigned page: {0u,600u}) for(bool swap: {false,true}) {
        fb_var_screeninfo v{};v.xres=1024;v.yres=600;v.xres_virtual=1024;v.yres_virtual=1200;v.bits_per_pixel=32;
        v.red={swap?16u:0u,8,0};v.green={8,8,0};v.blue={swap?0u:16u,8,0};v.transp={24,8,0};
        fb_fix_screeninfo f{};f.type=FB_TYPE_PACKED_PIXELS;f.visual=FB_VISUAL_TRUECOLOR;f.ypanstep=1;f.line_length=pitch;f.smem_len=pitch*1200;
        std::vector<unsigned char> src(stride*4*1024,0xe7),dst(f.smem_len+64,0x6a);
        for(unsigned y=0;y<1024;++y) for(unsigned x=0;x<600;++x) {
            size_t i=(size_t(y)*stride+x)*4;src[i]=x%251;src[i+1]=y%241;src[i+2]=(x+y)%239;src[i+3]=73;
        }
        assert(t110::copyPortraitFrame(dst.data(),f.smem_len,f,v,page,src.data(),src.size(),stride));
        // Independent forward mapping from each logical source pixel.
        for(unsigned sy=0;sy<1024;++sy) for(unsigned sx=0;sx<600;++sx) {
            unsigned nativeX=sy,nativeY=599-sx;size_t i=(size_t(page)+nativeY)*pitch+nativeX*4;
            assert(dst[i+(swap?2:0)]==sx%251);assert(dst[i+1]==sy%241);assert(dst[i+(swap?0:2)]==(sx+sy)%239);assert(dst[i+3]==255);
        }
        for(unsigned y=0;y<1200;++y) for(unsigned x=(y>=page&&y<page+600)?4096:0;x<pitch;++x) assert(dst[size_t(y)*pitch+x]==0x6a);
        for(size_t i=f.smem_len;i<dst.size();++i) assert(dst[i]==0x6a);
        auto saved=dst;
        assert(!t110::copyPortraitFrame(dst.data(),f.smem_len,f,v,page,src.data(),src.size()-1,stride));
        assert(!t110::copyPortraitFrame(dst.data(),f.smem_len,f,v,page,src.data(),src.size(),599));
        assert(!t110::copyPortraitFrame(dst.data(),4096,f,v,page,src.data(),src.size(),stride));
        assert(!t110::copyPortraitFrame(dst.data(),f.smem_len,f,v,601,src.data(),src.size(),stride));
        assert(!t110::copyPortraitFrame(dst.data(),f.smem_len,f,v,1200,src.data(),src.size(),stride));
        assert(!t110::copyPortraitFrame(dst.data(),f.smem_len,f,v,std::numeric_limits<unsigned>::max(),src.data(),src.size(),stride));
        assert(!t110::copyPortraitFrame(nullptr,f.smem_len,f,v,page,src.data(),src.size(),stride));
        assert(!t110::copyPortraitFrame(dst.data(),f.smem_len,f,v,page,nullptr,src.size(),stride));
        assert(dst==saved);
    }
    puts("PORTRAIT_SCANOUT_FULL_PIXEL_AND_BOUNDS_PASS");
}
