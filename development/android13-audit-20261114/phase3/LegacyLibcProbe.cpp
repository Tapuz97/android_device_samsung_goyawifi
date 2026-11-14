/* SPDX-License-Identifier: Apache-2.0 */
#include <dlfcn.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>

static void* shim;
static int checks;
#define CHECK(x) do { ++checks; if (!(x)) { std::fprintf(stderr, "FAIL %d: %s\n", __LINE__, #x); std::abort(); } } while (0)

template<class T> static T symbol(const char* name) {
    void* result=dlsym(shim, name);
    CHECK(result!=nullptr);
    return reinterpret_cast<T>(result);
}

static void divmod32(void* fn, uint32_t numerator, uint32_t denominator,
                     uint32_t* quotient, uint32_t* remainder) {
    register uint32_t a asm("r0")=numerator;
    register uint32_t b asm("r1")=denominator;
    asm volatile("blx %[fn]" : "+r"(a), "+r"(b) : [fn] "r"(fn)
                 : "r2", "r3", "ip", "lr", "cc", "memory", "d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7");
    *quotient=a; *remainder=b;
}

static void divmod64(void* fn, uint64_t numerator, uint64_t denominator,
                     uint64_t* quotient, uint64_t* remainder) {
    register uint32_t a asm("r0")=static_cast<uint32_t>(numerator);
    register uint32_t b asm("r1")=static_cast<uint32_t>(numerator>>32);
    register uint32_t c asm("r2")=static_cast<uint32_t>(denominator);
    register uint32_t d asm("r3")=static_cast<uint32_t>(denominator>>32);
    asm volatile("blx %[fn]" : "+r"(a), "+r"(b), "+r"(c), "+r"(d) : [fn] "r"(fn)
                 : "ip", "lr", "cc", "memory", "d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7");
    *quotient=static_cast<uint64_t>(a)|(static_cast<uint64_t>(b)<<32);
    *remainder=static_cast<uint64_t>(c)|(static_cast<uint64_t>(d)<<32);
}

int main() {
    shim=dlopen("/vendor/lib/libt110_audio_legacy_compat.so", RTLD_NOW|RTLD_LOCAL);
    if(!shim) { std::fprintf(stderr,"dlopen: %s\n",dlerror()); return 1; }
    // dlsym on the explicit shim handle forces our trampolines, rather than
    // allowing libc's global exports to satisfy calls before reaching them.
    for(int phase=0;phase<2;++phase) {
        CHECK(symbol<float(*)(double)>("__aeabi_d2f")(1.25)==1.25f);
        CHECK(symbol<int(*)(double)>("__aeabi_d2iz")(-2.9)==-2);
        CHECK(symbol<double(*)(double,double)>("__aeabi_dadd")(1.5,2.25)==3.75);
        CHECK(symbol<double(*)(double,double)>("__aeabi_dmul")(-2.0,1.25)==-2.5);
        CHECK(symbol<double(*)(float)>("__aeabi_f2d")(1.5f)==1.5);
        CHECK(symbol<int(*)(float)>("__aeabi_f2iz")(-1.75f)==-1);
        CHECK(symbol<float(*)(float,float)>("__aeabi_fadd")(1.25f,2.5f)==3.75f);
        CHECK(symbol<int(*)(float,float)>("__aeabi_fcmpeq")(2.0f,2.0f)==1);
        CHECK(symbol<int(*)(float,float)>("__aeabi_fcmpeq")(1.0f,2.0f)==0);
        CHECK(symbol<int(*)(float,float)>("__aeabi_fcmpgt")(3.0f,2.0f)==1);
        CHECK(symbol<int(*)(float,float)>("__aeabi_fcmpgt")(1.0f,2.0f)==0);
        CHECK(symbol<int(*)(float,float)>("__aeabi_fcmplt")(1.0f,2.0f)==1);
        CHECK(symbol<int(*)(float,float)>("__aeabi_fcmplt")(3.0f,2.0f)==0);
        CHECK(symbol<float(*)(float,float)>("__aeabi_fdiv")(7.5f,2.5f)==3.0f);
        CHECK(symbol<float(*)(float,float)>("__aeabi_fmul")(-1.5f,2.0f)==-3.0f);
        CHECK(symbol<float(*)(float,float)>("__aeabi_fsub")(1.5f,0.5f)==1.0f);
        CHECK(symbol<double(*)(int)>("__aeabi_i2d")(-257)==-257.0);
        CHECK(symbol<float(*)(int)>("__aeabi_i2f")(-257)==-257.0f);
        CHECK(symbol<int(*)(int,int)>("__aeabi_idiv")(-19,3)==-6);
        CHECK(symbol<double(*)(int64_t)>("__aeabi_l2d")((INT64_C(1)<<35)+1)==34359738369.0);
        CHECK(symbol<uint64_t(*)(uint64_t,int)>("__aeabi_llsl")(1,37)==UINT64_C(137438953472));
        CHECK(symbol<unsigned(*)(unsigned,unsigned)>("__aeabi_uidiv")(19,3)==6);
        CHECK(symbol<int(*)(unsigned)>("__popcountsi2")(0xf01234ffu)==17);
        uint32_t q32,r32;
        divmod32(symbol<void*>("__aeabi_idivmod"),static_cast<uint32_t>(-19),3,&q32,&r32);
        CHECK(static_cast<int32_t>(q32)==-6 && static_cast<int32_t>(r32)==-1);
        divmod32(symbol<void*>("__aeabi_uidivmod"),19,3,&q32,&r32);
        CHECK(q32==6 && r32==1);
        uint64_t q64,r64;
        constexpr int64_t sn=-100000000001LL,sd=7;
        divmod64(symbol<void*>("__aeabi_ldivmod"),static_cast<uint64_t>(sn),sd,&q64,&r64);
        CHECK(static_cast<int64_t>(q64)==sn/sd && static_cast<int64_t>(r64)==sn%sd);
        constexpr uint64_t un=UINT64_C(0x123456789abcdef),ud=37;
        divmod64(symbol<void*>("__aeabi_uldivmod"),un,ud,&q64,&r64);
        CHECK(q64==un/ud && r64==un%ud);
        FILE* file=std::tmpfile();
        CHECK(file!=nullptr);
        CHECK(symbol<int(*)(int,FILE*)>("__swbuf")('Q',file)=='Q');
        CHECK(std::fflush(file)==0);
        std::rewind(file);
        CHECK(symbol<int(*)(FILE*)>("__srget")(file)=='Q');
        CHECK(std::fclose(file)==0);
    }
    std::printf("PASS: 26 exact Bionic helper trampolines, cold/warm paths, ARM multi-register divmod and FILE IO (%d checks)\n",checks);
    return 0;
}
