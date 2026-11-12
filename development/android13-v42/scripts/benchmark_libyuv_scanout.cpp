#define t110 t110_reference
#include "../work/T110Scanout.h"
#undef t110
#define t110 t110_optimized
#include "../evidence/offline-v39/T110Scanout-libyuv.h"
#undef t110
#include <cassert>
#include <cstdio>
#include <vector>
#include <ctime>

static double now() {
    timespec t{};clock_gettime(CLOCK_MONOTONIC,&t);
    return t.tv_sec+t.tv_nsec/1e9;
}
int main() {
    for(unsigned stride:{600u,608u,640u})for(unsigned pitch:{4096u,4224u})
    for(unsigned page:{0u,600u})for(unsigned alpha:{0u,8u})for(bool swap:{false,true}) {
        fb_var_screeninfo v{};v.xres=1024;v.yres=600;v.xres_virtual=1024;v.yres_virtual=1200;v.bits_per_pixel=32;
        v.red={swap?16u:0u,8,0};v.green={8,8,0};v.blue={swap?0u:16u,8,0};v.transp={24,alpha,0};
        fb_fix_screeninfo f{};f.type=FB_TYPE_PACKED_PIXELS;f.visual=FB_VISUAL_TRUECOLOR;f.ypanstep=1;f.line_length=pitch;f.smem_len=pitch*1200;
        std::vector<unsigned char> src(stride*4*1024,0xe7),a(f.smem_len+64,0x6a),b(a);
        for(unsigned y=0;y<1024;++y)for(unsigned x=0;x<600;++x){size_t i=(size_t(y)*stride+x)*4;src[i]=x%251;src[i+1]=y%241;src[i+2]=(x+y)%239;src[i+3]=73;}
        assert(t110_reference::copyPortraitFrame(a.data(),f.smem_len,f,v,page,src.data(),src.size(),stride));
        assert(t110_optimized::copyPortraitFrame(b.data(),f.smem_len,f,v,page,src.data(),src.size(),stride));
        assert(a==b);
        auto saved=b;
        assert(!t110_optimized::copyPortraitFrame(b.data(),f.smem_len,f,v,page,src.data(),src.size()-1,stride));
        assert(!t110_optimized::copyPortraitFrame(b.data(),4096,f,v,page,src.data(),src.size(),stride));
        assert(!t110_optimized::copyPortraitFrame(b.data(),f.smem_len,f,v,601,src.data(),src.size(),stride));
        assert(!t110_optimized::copyPortraitFrame(nullptr,f.smem_len,f,v,page,src.data(),src.size(),stride));
        assert(b==saved);
        if(stride==608&&pitch==4096&&page==0&&alpha==0&&swap) {
            constexpr int count=16;
            double start=now();
            for(int n=0;n<count;n++)assert(t110_reference::copyPortraitFrame(a.data(),f.smem_len,f,v,page,src.data(),src.size(),stride));
            double baseline=1000*(now()-start)/count;
            start=now();
            for(int n=0;n<count;n++)assert(t110_optimized::copyPortraitFrame(b.data(),f.smem_len,f,v,page,src.data(),src.size(),stride));
            printf("reference_ms=%.4f libyuv_ms=%.4f\n",baseline,1000*(now()-start)/count);
        }
    }
    puts("FULL_PIXEL_PADDING_ALPHA_AND_BOUNDS_PASS");return 0;
}
