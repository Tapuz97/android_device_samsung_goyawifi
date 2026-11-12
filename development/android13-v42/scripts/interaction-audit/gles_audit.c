/* Test-app-only Android GLES layer. Forward calls and preserve observed errors. */
typedef unsigned int U;
typedef int I;
typedef unsigned char B;
typedef float F;
typedef long Size;
typedef void (*Fn)(void);
#ifndef T110_AUDIT_RESOLVE_MODE
#define T110_AUDIT_RESOLVE_MODE 3
#endif
extern int strcmp(const char *,const char *);
extern int __android_log_print(int,const char *,const char *,...);
#define LOG(...) __android_log_print(4,"T110GlesAudit",__VA_ARGS__)
static void *layer;
static void *(*getnext)(void *,const char *);
static U (*driver_error)(void);
static void (*driver_integer)(U,I *);
static void (*driver_boolean)(U,B *);
static void (*driver_shader_iv)(U,U,I *);
static void (*driver_program_iv)(U,U,I *);
static void (*driver_shader_log)(U,I,I *,char *);
static void (*driver_program_log)(U,I,I *,char *);
static void (*driver_finish)(void);
static void (*driver_read_pixels)(I,I,I,I,U,U,void *);
static __thread U errors[32];
static __thread I error_count;
static void observe(const char *name) {
    if (!driver_error) return;
    for(I i=0;i<16;++i) {
        U e=driver_error();if(!e)break;
        LOG("%s GL_ERROR=0x%x",name,e);
        I found=0;for(I j=0;j<error_count;++j)found|=errors[j]==e;
        if(!found && error_count<32)errors[error_count++]=e;
    }
}
static U audit_glGetError(void) {
    if(error_count){U e=errors[0];for(I i=1;i<error_count;++i)errors[i-1]=errors[i];--error_count;return e;}
    return driver_error();
}
static void state(const char *name) {
    I vp[4]={0},sc[4]={0},program=0,fbo=0,vbo=0,ibo=0;B mask[4]={0};
    driver_integer(0x0ba2,vp);driver_integer(0x0c10,sc);
    driver_integer(0x8b8d,&program);driver_integer(0x8ca6,&fbo);
    driver_integer(0x8894,&vbo);driver_integer(0x8895,&ibo);driver_boolean(0x0c23,mask);
    LOG("%s state prog=%d fbo=%d vbo=%d ibo=%d viewport=%d,%d,%d,%d scissor=%d,%d,%d,%d mask=%d%d%d%d",
        name,program,fbo,vbo,ibo,vp[0],vp[1],vp[2],vp[3],sc[0],sc[1],sc[2],sc[3],mask[0],mask[1],mask[2],mask[3]);
}
static void read_draw_result(void) {
    if(T110_AUDIT_RESOLVE_MODE==1){driver_finish();LOG("after-draw-finish-only");return;}
    if(T110_AUDIT_RESOLVE_MODE>=4)return;
    I viewport[4]={0};driver_integer(0x0ba2,viewport);
    if(viewport[0]||viewport[1]||viewport[2]!=64||viewport[3]!=64)return;
    /* Diagnostic only: force completion BEFORE presentation and inspect this
     * tiny fixture's buffer. Never enable this layer for production apps. */
    B pixels[64*64*4];I red=0,green=0,other=0;
    if(T110_AUDIT_RESOLVE_MODE!=2)driver_finish();
    driver_read_pixels(0,0,64,64,0x1908,0x1401,pixels);
    for(I i=0;i<64*64;++i){B *p=pixels+4*i;
        if(p[0]==255&&p[1]==0&&p[2]==0)red++;
        else if(p[0]==0&&p[1]==255&&p[2]==0)green++;else other++;
    }
    LOG("preswap-draw-readback red=%d green=%d other=%d",red,green,other);
}
#define VOID_HOOK(name,params,args,...) \
    static void (*next_##name) params; \
    static void audit_##name params {LOG(#name " " __VA_ARGS__);next_##name args;observe(#name);}
VOID_HOOK(glClear,(U bits),(bits),"bits=%x",bits)
VOID_HOOK(glViewport,(I x,I y,I w,I h),(x,y,w,h),"%d %d %d %d",x,y,w,h)
VOID_HOOK(glScissor,(I x,I y,I w,I h),(x,y,w,h),"%d %d %d %d",x,y,w,h)
VOID_HOOK(glEnable,(U value),(value),"%x",value)
VOID_HOOK(glDisable,(U value),(value),"%x",value)
VOID_HOOK(glBindFramebuffer,(U target,U fbo),(target,fbo),"target=%x id=%u",target,fbo)
VOID_HOOK(glBindBuffer,(U target,U buffer),(target,buffer),"target=%x id=%u",target,buffer)
VOID_HOOK(glBufferData,(U target,Size size,const void *data,U usage),(target,size,data,usage),"target=%x size=%ld data=%p usage=%x",target,size,data,usage)
static void (*next_glBufferSubData)(U,Size,Size,const void *);
static void audit_glBufferSubData(U target,Size offset,Size size,const void *data) {
    LOG("glBufferSubData target=%x offset=%ld size=%ld data=%p",target,offset,size,data);
    if(data&&size>=48) {
        U words[12];__builtin_memcpy(words,data,sizeof(words));
        LOG("vertex-data first48bytes=%08x,%08x,%08x;%08x,%08x,%08x;%08x,%08x,%08x;%08x,%08x,%08x",
            words[0],words[1],words[2],words[3],words[4],words[5],words[6],words[7],words[8],words[9],words[10],words[11]);
    }
    next_glBufferSubData(target,offset,size,data);observe("glBufferSubData");
}
VOID_HOOK(glUseProgram,(U program),(program),"id=%u",program)
VOID_HOOK(glFlush,(void),(),"flush")
VOID_HOOK(glFinish,(void),(),"finish")
VOID_HOOK(glDiscardFramebufferEXT,(U target,I count,const U *attachments),(target,count,attachments),"target=%x count=%d first=%x",target,count,count>0?attachments[0]:0)
VOID_HOOK(glInvalidateFramebuffer,(U target,I count,const U *attachments),(target,count,attachments),"target=%x count=%d first=%x",target,count,count>0?attachments[0]:0)
static I (*next_glGetUniformLocation)(U,const char *);
static I audit_glGetUniformLocation(U program,const char *name) {
    I location=next_glGetUniformLocation(program,name);LOG("uniform program=%u name=%s location=%d",program,name,location);return location;
}
static void (*next_glUniform4fv)(I,I,const F *);
static void audit_glUniform4fv(I location,I count,const F *data) {
    U bits[4]={0};if(data&&count>0)__builtin_memcpy(bits,data,sizeof(bits));
    LOG("glUniform4fv loc=%d count=%d bits=%08x,%08x,%08x,%08x",location,count,bits[0],bits[1],bits[2],bits[3]);
    next_glUniform4fv(location,count,data);observe("glUniform4fv");
}
VOID_HOOK(glEnableVertexAttribArray,(U index),(index),"index=%u",index)
VOID_HOOK(glDisableVertexAttribArray,(U index),(index),"index=%u",index)
VOID_HOOK(glVertexAttribPointer,(U index,I size,U type,B norm,I stride,const void *pointer),(index,size,type,norm,stride,pointer),"index=%u size=%d type=%x norm=%d stride=%d pointer=%p",index,size,type,norm,stride,pointer)
static void (*next_glDrawArrays)(U,I,I);
static void audit_glDrawArrays(U mode,I first,I count) {
    state("glDrawArrays");LOG("glDrawArrays mode=%x first=%d count=%d",mode,first,count);
    next_glDrawArrays(mode,first,count);read_draw_result();observe("glDrawArrays");
}
static void (*next_glDrawElements)(U,I,U,const void *);
static void audit_glDrawElements(U mode,I count,U type,const void *indices) {
    state("glDrawElements");LOG("glDrawElements mode=%x count=%d type=%x indices=%p",mode,count,type,indices);
    next_glDrawElements(mode,count,type,indices);read_draw_result();observe("glDrawElements");
}
static void (*next_glShaderSource)(U,I,const char *const *,const I *);
static void audit_glShaderSource(U shader,I count,const char *const *strings,const I *lengths) {
    for(I i=0;i<count;++i){I n=lengths&&lengths[i]>=0?lengths[i]:1800;if(n>1800)n=1800;
        LOG("shader=%u source[%d]=%.*s",shader,i,n,strings[i]);}
    next_glShaderSource(shader,count,strings,lengths);observe("glShaderSource");
}
static void (*next_glCompileShader)(U);
static void audit_glCompileShader(U shader) {
    next_glCompileShader(shader);observe("glCompileShader");I ok=0;char text[768]={0};
    driver_shader_iv(shader,0x8b81,&ok);driver_shader_log(shader,sizeof(text)-1,0,text);
    LOG("compile shader=%u ok=%d info=%s",shader,ok,text);
}
static void (*next_glLinkProgram)(U);
static void audit_glLinkProgram(U program) {
    next_glLinkProgram(program);observe("glLinkProgram");I ok=0;char text[768]={0};
    driver_program_iv(program,0x8b82,&ok);driver_program_log(program,sizeof(text)-1,0,text);
    LOG("link program=%u ok=%d info=%s",program,ok,text);
}
static U (*next_eglSwapBuffers)(void *,void *);
static void before_swap(void) {
    if(T110_AUDIT_RESOLVE_MODE==4)driver_finish();
    if(T110_AUDIT_RESOLVE_MODE==6){B pixel[4];driver_read_pixels(0,0,1,1,0x1908,0x1401,pixel);LOG("preswap-one-pixel-resolve");}
}
static void *(*next_eglCreateSyncKHR)(void *,U,const I *);
static void *audit_eglCreateSyncKHR(void *display,U type,const I *attrs) {
    void *sync=next_eglCreateSyncKHR(display,type,attrs);LOG("eglCreateSyncKHR type=%x sync=%p",type,sync);return sync;
}
static I (*next_eglClientWaitSyncKHR)(void *,void *,I,unsigned long long);
static I audit_eglClientWaitSyncKHR(void *display,void *sync,I flags,unsigned long long timeout) {
    LOG("eglClientWaitSyncKHR begin sync=%p flags=%x timeout=%llu",sync,flags,timeout);
    I value=next_eglClientWaitSyncKHR(display,sync,flags,timeout);LOG("eglClientWaitSyncKHR result=%x",value);return value;
}
static U (*next_eglDestroySyncKHR)(void *,void *);
static U audit_eglDestroySyncKHR(void *display,void *sync) {
    U value=next_eglDestroySyncKHR(display,sync);LOG("eglDestroySyncKHR sync=%p result=%u",sync,value);return value;
}
static U audit_eglSwapBuffers(void *display,void *surface) {
    before_swap();
    U value=next_eglSwapBuffers(display,surface);LOG("eglSwapBuffers result=%u",value);return value;
}
static U (*next_eglSwapBuffersWithDamageKHR)(void *,void *,const I *,I);
static U audit_eglSwapBuffersWithDamageKHR(void *display,void *surface,const I *rects,I count) {
    if(T110_AUDIT_RESOLVE_MODE==5){U result=next_eglSwapBuffers(display,surface);LOG("legacy-full-swap result=%u",result);return result;}
    before_swap();
    U value=next_eglSwapBuffersWithDamageKHR(display,surface,rects,count);
    LOG("eglSwapBuffersWithDamageKHR count=%d result=%u",count,value);return value;
}
static void *(*next_glMapBufferRange)(U,Size,Size,U);
static void *audit_glMapBufferRange(U target,Size offset,Size size,U access) {
    void *result=next_glMapBufferRange(target,offset,size,access);
    LOG("glMapBufferRange target=%x offset=%ld size=%ld access=%x result=%p",target,offset,size,access,result);
    observe("glMapBufferRange");return result;
}
__attribute__((visibility("default"))) void AndroidGLESLayer_Initialize(void *id,void *(*next)(void *,const char *)) {
    layer=id;getnext=next;LOG("initialized scoped GLES trace mode=%d",T110_AUDIT_RESOLVE_MODE);
    driver_error=getnext(layer,"glGetError");driver_integer=getnext(layer,"glGetIntegerv");
    driver_boolean=getnext(layer,"glGetBooleanv");driver_shader_iv=getnext(layer,"glGetShaderiv");
    driver_program_iv=getnext(layer,"glGetProgramiv");driver_shader_log=getnext(layer,"glGetShaderInfoLog");
    driver_program_log=getnext(layer,"glGetProgramInfoLog");
    driver_finish=getnext(layer,"glFinish");driver_read_pixels=getnext(layer,"glReadPixels");
}
__attribute__((visibility("default"))) void *AndroidGLESLayer_GetProcAddress(const char *name,Fn next) {
    if(!strcmp(name,"glGetError"))return (void *)audit_glGetError;
#define HOOK(f) if(!strcmp(name,#f)){next_##f=(void *)next;return (void *)audit_##f;}
    HOOK(glClear) HOOK(glViewport) HOOK(glScissor) HOOK(glEnable) HOOK(glDisable)
    HOOK(glBindFramebuffer) HOOK(glBindBuffer) HOOK(glBufferData) HOOK(glBufferSubData)
    HOOK(glUseProgram) HOOK(glEnableVertexAttribArray) HOOK(glDisableVertexAttribArray)
    HOOK(glVertexAttribPointer) HOOK(glDrawArrays) HOOK(glDrawElements)
    HOOK(glShaderSource) HOOK(glCompileShader) HOOK(glLinkProgram)
    HOOK(eglSwapBuffers) HOOK(eglSwapBuffersWithDamageKHR) HOOK(glMapBufferRange)
    HOOK(glUniform4fv) HOOK(glGetUniformLocation) HOOK(glFlush) HOOK(glFinish)
    HOOK(glDiscardFramebufferEXT) HOOK(glInvalidateFramebuffer)
    HOOK(eglCreateSyncKHR) HOOK(eglClientWaitSyncKHR) HOOK(eglDestroySyncKHR)
    return (void *)next;
}
