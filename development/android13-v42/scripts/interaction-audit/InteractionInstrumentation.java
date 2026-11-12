package dev.tapuz.t110.interaction;

import android.app.Instrumentation;
import android.app.UiAutomation;
import android.net.*;
import android.graphics.*;
import android.media.Image;
import android.media.ImageReader;
import android.hardware.HardwareBuffer;
import android.opengl.*;
import android.os.*;
import android.view.InputDevice;
import android.view.MotionEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import org.json.*;
import java.net.*;
import javax.net.ssl.HttpsURLConnection;
import java.util.*;

/** Temporary test-only instrumentation. No launcher icon or ROM modifications. */
public final class InteractionInstrumentation extends Instrumentation {
    Bundle args;
    JSONObject colors(java.nio.ByteBuffer data,int width,int height,int row,int pixel) throws Exception {
        int red=0,green=0,other=0;
        for(int y=0;y<height;y++)for(int x=0;x<width;x++) {
            int at=y*row+x*pixel;int r=data.get(at)&255,g=data.get(at+1)&255,b=data.get(at+2)&255;
            if(r==255&&g==0&&b==0)red++;else if(r==0&&g==255&&b==0)green++;else other++;
        }
        return new JSONObject().put("red",red).put("green",green).put("other",other)
            .put("correct",red==width*height/2&&green==width*height/2&&other==0);
    }
    int shader(int type,String source) {
        int shader=GLES20.glCreateShader(type);GLES20.glShaderSource(shader,source);GLES20.glCompileShader(shader);
        int[] ok=new int[1];GLES20.glGetShaderiv(shader,GLES20.GL_COMPILE_STATUS,ok,0);
        if(ok[0]!=1)throw new IllegalStateException(GLES20.glGetShaderInfoLog(shader));return shader;
    }
    void drawFixture(Canvas canvas,int width,int height,int phase,Bitmap tile) {
        Paint p=new Paint();p.setAntiAlias(false);p.setFilterBitmap(false);
        canvas.drawColor(phase==1?Color.BLUE:Color.RED);
        if(phase==0){p.setColor(Color.GREEN);canvas.drawRect(width/2,0,width,height,p);}
        else if(phase==1){
            canvas.save();canvas.clipRect(width/4,height/4,3*width/4,3*height/4);
            canvas.translate(width/2,height/2);p.setColor(Color.GREEN);
            canvas.drawRect(-width/2,-height/2,width/2,height/2,p);canvas.restore();
        }else if(phase==2){
            canvas.drawBitmap(tile,null,new Rect(0,0,width/2,height),p);
            p.setColor(Color.YELLOW);canvas.drawRect(width/2,0,width,height,p);
        }else if(phase==3){
            canvas.saveLayerAlpha(0,0,width,height,128);
            p.setColor(Color.GREEN);canvas.drawRect(width/4,height/4,3*width/4,3*height/4,p);
            canvas.restore();
        }else{
            p.setColor(Color.WHITE);p.setTextSize(width/8);p.setSubpixelText(false);
            canvas.drawText("T110",width/8,height/2,p);
            p.setColor(Color.BLUE);canvas.drawRoundRect(width/4,3*height/4,3*width/4,7*height/8,width/16,width/16,p);
        }
    }
    JSONObject hwuiSuite() throws Exception {
        int width=Integer.parseInt(args.getString("width","64")),height=Integer.parseInt(args.getString("height","64"));
        if(width<16||height<16||width>1024||height>1024||(long)width*height>614400)
            throw new IllegalArgumentException("Offscreen size exceeds audit bounds");
        Bitmap tile=Bitmap.createBitmap(new int[]{Color.RED,Color.GREEN,Color.BLUE,Color.WHITE},2,2,Bitmap.Config.ARGB_8888);
        JSONArray cases=new JSONArray();boolean all=true;
        try{
            for(int lifecycle=0;lifecycle<2;lifecycle++){
                ImageReader reader=ImageReader.newInstance(width,height,PixelFormat.RGBA_8888,2,
                    HardwareBuffer.USAGE_GPU_COLOR_OUTPUT|HardwareBuffer.USAGE_CPU_READ_OFTEN);
                HardwareRenderer renderer=new HardwareRenderer();
                try{
                    renderer.setSurface(reader.getSurface());renderer.setOpaque(true);
                    int phases="true".equals(args.getString("extended"))?5:3;
                    for(int phase=0;phase<phases;phase++){
                        Bitmap expected=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888);
                        drawFixture(new Canvas(expected),width,height,phase,tile);
                        RenderNode node=new RenderNode("T110 HWUI fixture "+phase);node.setPosition(0,0,width,height);
                        drawFixture(node.beginRecording(width,height),width,height,phase,tile);node.endRecording();renderer.setContentRoot(node);
                        long started=SystemClock.elapsedRealtime();
                        int draw=renderer.createRenderRequest().setWaitForPresent(true).syncAndDraw();
                        long renderMs=SystemClock.elapsedRealtime()-started;
                        Image image=null;
                        try{
                            for(int retry=0;retry<50&&image==null;retry++){image=reader.acquireLatestImage();if(image==null)SystemClock.sleep(100);}
                            if(image==null)throw new IllegalStateException("Fixture produced no image");
                            Image.Plane plane=image.getPlanes()[0];java.nio.ByteBuffer pixels=plane.getBuffer();
                            int[] reference=new int[width*height];expected.getPixels(reference,0,width,0,0,width,height);
                            long comparisonStarted=SystemClock.elapsedRealtime();
                            int wrong=0;JSONArray wrongSamples=new JSONArray();
                            for(int y=0;y<height;y++)for(int x=0;x<width;x++){
                                int at=y*plane.getRowStride()+x*plane.getPixelStride(),color=reference[y*width+x];
                                int tolerance=phase>=3?1:0;
                                if(Math.abs((pixels.get(at)&255)-Color.red(color))>tolerance||Math.abs((pixels.get(at+1)&255)-Color.green(color))>tolerance
                                    ||Math.abs((pixels.get(at+2)&255)-Color.blue(color))>tolerance||Math.abs((pixels.get(at+3)&255)-Color.alpha(color))>tolerance){
                                    wrong++;
                                    if(wrongSamples.length()<40)wrongSamples.put(new JSONObject().put("x",x).put("y",y).put("expected_argb",Integer.toHexString(color))
                                        .put("actual_rgba",new JSONArray(new int[]{pixels.get(at)&255,pixels.get(at+1)&255,pixels.get(at+2)&255,pixels.get(at+3)&255})));
                                }
                            }
                            all&=wrong==0;
                            cases.put(new JSONObject().put("lifecycle",lifecycle).put("phase",phase).put("draw_result",draw)
                                .put("wrong_pixels",wrong).put("wrong_samples",wrongSamples).put("pixel_count",width*height).put("render_request_ms",renderMs)
                                .put("pixel_comparison_ms",SystemClock.elapsedRealtime()-comparisonStarted).put("elapsed_ms",SystemClock.elapsedRealtime()-started));
                        }finally{if(image!=null)image.close();expected.recycle();}
                    }
                }finally{renderer.destroy();reader.close();}
            }
        }finally{tile.recycle();}
        return new JSONObject().put("target_size",width+"x"+height).put("all_pixels_match",all).put("cases",cases)
            .put("production_window_policy_changed",false);
    }
    JSONObject rawGles() throws Exception {
        int width=64,height=64;
        boolean skiaLike="true".equals(args.getString("skiaLike"));
        ImageReader reader=ImageReader.newInstance(width,height,PixelFormat.RGBA_8888,2,
            HardwareBuffer.USAGE_GPU_COLOR_OUTPUT|HardwareBuffer.USAGE_CPU_READ_OFTEN);
        EGLDisplay display=EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);
        EGLContext context=EGL14.EGL_NO_CONTEXT;EGLSurface surface=EGL14.EGL_NO_SURFACE;
        JSONObject report=new JSONObject().put("skia_state_replay",skiaLike);
        try {
            int[] version=new int[2];if(!EGL14.eglInitialize(display,version,0,version,1))throw new IllegalStateException("EGL initialize "+EGL14.eglGetError());
            EGLConfig[] config=new EGLConfig[1];int[] count=new int[1];
            int[] attributes={EGL14.EGL_RED_SIZE,8,EGL14.EGL_GREEN_SIZE,8,EGL14.EGL_BLUE_SIZE,8,EGL14.EGL_ALPHA_SIZE,8,
                EGL14.EGL_RENDERABLE_TYPE,EGL14.EGL_OPENGL_ES2_BIT,EGL14.EGL_SURFACE_TYPE,EGL14.EGL_WINDOW_BIT,EGL14.EGL_NONE};
            if(!EGL14.eglChooseConfig(display,attributes,0,config,0,1,count,0)||count[0]<1)throw new IllegalStateException("No RGBA8 window EGL config");
            context=EGL14.eglCreateContext(display,config[0],EGL14.EGL_NO_CONTEXT,new int[]{EGL14.EGL_CONTEXT_CLIENT_VERSION,2,EGL14.EGL_NONE},0);
            surface=EGL14.eglCreateWindowSurface(display,config[0],reader.getSurface(),new int[]{EGL14.EGL_NONE},0);
            if(context==EGL14.EGL_NO_CONTEXT||surface==EGL14.EGL_NO_SURFACE||!EGL14.eglMakeCurrent(display,surface,surface,context))
                throw new IllegalStateException("EGL context/window "+EGL14.eglGetError());
            report.put("renderer",GLES20.glGetString(GLES20.GL_RENDERER)).put("version",GLES20.glGetString(GLES20.GL_VERSION));
            String vertex="#version 100\nprecision mediump float;\nuniform highp vec4 sk_RTAdjust;\nattribute highp vec2 position;\nattribute mediump vec4 color;\nvarying mediump vec4 vcolor_S0;\nvoid main(){vcolor_S0=color;gl_Position=vec4(position,0.0,1.0);gl_Position=vec4(gl_Position.xy*sk_RTAdjust.xz+gl_Position.ww*sk_RTAdjust.yw,0.0,gl_Position.w);}";
            String fragment="#version 100\nprecision mediump float;\nvarying mediump vec4 vcolor_S0;\nvoid main(){gl_FragColor=vcolor_S0;}";
            if(skiaLike)fragment="#version 100\nprecision mediump float;\nprecision mediump sampler2D;\nvarying mediump vec4 vcolor_S0;\nvoid main(){mediump vec4 outputColor_S0;outputColor_S0=vcolor_S0;{gl_FragColor=outputColor_S0;}}";
            int vs=shader(GLES20.GL_VERTEX_SHADER,vertex),fs=shader(GLES20.GL_FRAGMENT_SHADER,fragment),program=GLES20.glCreateProgram();
            GLES20.glAttachShader(program,vs);GLES20.glAttachShader(program,fs);
            GLES20.glBindAttribLocation(program,0,"position");GLES20.glBindAttribLocation(program,1,"color");GLES20.glLinkProgram(program);
            int[] ok=new int[1];GLES20.glGetProgramiv(program,GLES20.GL_LINK_STATUS,ok,0);
            if(ok[0]!=1)throw new IllegalStateException(GLES20.glGetProgramInfoLog(program));
            GLES20.glUseProgram(program);GLES20.glUniform4fv(GLES20.glGetUniformLocation(program,"sk_RTAdjust"),1,new float[]{2f/width,-1,-2f/height,1},0);
            java.nio.ByteBuffer vertices=java.nio.ByteBuffer.allocateDirect(skiaLike?32768:48).order(java.nio.ByteOrder.nativeOrder());
            for(float[] xy:new float[][]{{32,0},{32,64},{64,0},{64,64}}){vertices.putFloat(xy[0]);vertices.putFloat(xy[1]);vertices.put(new byte[]{0,(byte)255,0,(byte)255});}
            vertices.position(0);int[] buffer=new int[1];GLES20.glGenBuffers(1,buffer,0);JSONArray cases=new JSONArray();
            for(int mode=0;mode<3;mode++) {
                JSONObject item=new JSONObject().put("mode",new String[]{"client-arrays","vbo-upload","vbo-orphan-subdata"}[mode]);
                GLES20.glViewport(0,0,width,height);GLES20.glDisable(GLES20.GL_SCISSOR_TEST);GLES20.glDisable(GLES20.GL_DEPTH_TEST);
                GLES20.glDisable(GLES20.GL_CULL_FACE);GLES20.glDisable(GLES20.GL_BLEND);GLES20.glClearColor(1,0,0,1);GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);
                if(skiaLike){GLES20.glEnable(GLES20.GL_BLEND);GLES20.glBlendFuncSeparate(GLES20.GL_ONE,GLES20.GL_ONE_MINUS_SRC_ALPHA,GLES20.GL_ONE,GLES20.GL_ONE_MINUS_SRC_ALPHA);
                    GLES20.glBlendEquationSeparate(GLES20.GL_FUNC_ADD,GLES20.GL_FUNC_ADD);for(int index=2;index<10;index++)GLES20.glDisableVertexAttribArray(index);}
                GLES20.glEnableVertexAttribArray(0);GLES20.glEnableVertexAttribArray(1);vertices.position(0);
                if(mode==0) {
                    GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER,0);
                    GLES20.glVertexAttribPointer(0,2,GLES20.GL_FLOAT,false,12,vertices);
                    vertices.position(8);GLES20.glVertexAttribPointer(1,4,GLES20.GL_UNSIGNED_BYTE,true,12,vertices);vertices.position(0);
                } else {
                    GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER,buffer[0]);
                    GLES20.glBufferData(GLES20.GL_ARRAY_BUFFER,vertices.capacity(),mode==1?vertices:null,GLES20.GL_STREAM_DRAW);
                    if(skiaLike&&mode==2)GLES20.glBufferData(GLES20.GL_ARRAY_BUFFER,vertices.capacity(),null,GLES20.GL_STREAM_DRAW);
                    if(mode==2)GLES20.glBufferSubData(GLES20.GL_ARRAY_BUFFER,0,48,vertices);
                    GLES20.glVertexAttribPointer(0,2,GLES20.GL_FLOAT,false,12,0);GLES20.glVertexAttribPointer(1,4,GLES20.GL_UNSIGNED_BYTE,true,12,8);
                }
                GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP,0,4);GLES20.glFinish();
                java.nio.ByteBuffer pixels=java.nio.ByteBuffer.allocateDirect(width*height*4);
                GLES20.glReadPixels(0,0,width,height,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,pixels);
                item.put("framebuffer",colors(pixels,width,height,width*4,4)).put("gl_error",GLES20.glGetError());
                item.put("swap",EGL14.eglSwapBuffers(display,surface));GLES20.glFinish();
                Image image=null;
                for(int retry=0;retry<30&&image==null;retry++){image=reader.acquireLatestImage();if(image==null)SystemClock.sleep(100);}
                if(image==null)item.put("queued_image","not received");
                else try {Image.Plane plane=image.getPlanes()[0];item.put("queued_image",colors(plane.getBuffer(),width,height,plane.getRowStride(),plane.getPixelStride()));}finally{image.close();}
                cases.put(item);
            }
            report.put("cases",cases);GLES20.glDeleteBuffers(1,buffer,0);GLES20.glDeleteProgram(program);GLES20.glDeleteShader(vs);GLES20.glDeleteShader(fs);
        } finally {
            if(display!=EGL14.EGL_NO_DISPLAY){EGL14.eglMakeCurrent(display,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_CONTEXT);
                if(surface!=EGL14.EGL_NO_SURFACE)EGL14.eglDestroySurface(display,surface);if(context!=EGL14.EGL_NO_CONTEXT)EGL14.eglDestroyContext(display,context);EGL14.eglTerminate(display);}
            reader.close();
        }
        return report;
    }
    public void onCreate(Bundle b) { args=b; start(); }
    AccessibilityNodeInfo root(UiAutomation ui) {
        for(int i=0;i<30;i++) {
            AccessibilityNodeInfo n=ui.getRootInActiveWindow();
            if(n!=null)return n;
            SystemClock.sleep(200);
        }
        throw new IllegalStateException("No active accessibility window");
    }
    void visit(AccessibilityNodeInfo n,JSONArray out,String target,List<AccessibilityNodeInfo> found) throws Exception {
        String text=n.isPassword()?"<redacted>":String.valueOf(n.getText());
        String desc=n.isPassword()?"<redacted>":String.valueOf(n.getContentDescription());
        android.graphics.Rect b=new android.graphics.Rect();n.getBoundsInScreen(b);
        if(!"null".equals(text)||!"null".equals(desc)||n.isClickable())
            out.put(new JSONObject().put("text",text).put("description",desc)
                .put("resource",n.getViewIdResourceName()).put("clickable",n.isClickable())
                .put("bounds",new JSONArray(new int[]{b.left,b.top,b.right,b.bottom})));
        boolean prefix="true".equals(args.getString("prefix"));
        if(!n.isPassword()&&target!=null&&(target.equals(text)||target.equals(desc)
                ||(prefix&&text.startsWith(target))))found.add(n);
        for(int i=0;i<n.getChildCount();i++){AccessibilityNodeInfo c=n.getChild(i);if(c!=null)visit(c,out,target,found);}
    }
    public void onStart() {
        JSONObject result=new JSONObject();
        try {
            String action=args.getString("action","dump");result.put("action",action).put("pid",android.os.Process.myPid());
            if("bluetooth".equals(action)) {
                result.put("bluetooth",PeripheralAudit.bluetooth(getTargetContext(),"true".equals(args.getString("stateOnly"))));
            } else if("storage".equals(action)) {
                result.put("storage",PeripheralAudit.storage(getTargetContext()));
            } else if("hwui-suite".equals(action)) {
                result.put("hwui_suite",hwuiSuite());
            } else if("gles".equals(action)) {
                result.put("raw_gles",rawGles());
            } else if("hwui".equals(action)) {
                // Isolated offscreen target, bounded to the panel pixel count.
                int width=Integer.parseInt(args.getString("width","64"));
                int height=Integer.parseInt(args.getString("height","64"));
                if(width<16||height<16||width>1024||height>1024||(long)width*height>614400)
                    throw new IllegalArgumentException("Offscreen size exceeds audit bounds");
                ImageReader reader=ImageReader.newInstance(width,height,PixelFormat.RGBA_8888,2,
                        HardwareBuffer.USAGE_GPU_COLOR_OUTPUT|HardwareBuffer.USAGE_CPU_READ_OFTEN);
                HardwareRenderer renderer=new HardwareRenderer();Image image=null;
                try {
                    renderer.setSurface(reader.getSurface());renderer.setOpaque(true);
                    RenderNode node=new RenderNode("T110 isolated HWUI audit");node.setPosition(0,0,width,height);
                    RecordingCanvas canvas=node.beginRecording(width,height);canvas.drawColor(Color.RED);
                    Paint paint=new Paint();paint.setColor(Color.GREEN);canvas.drawRect(width/2,0,width,height,paint);
                    node.endRecording();renderer.setContentRoot(node);
                    HardwareRenderer.FrameRenderRequest request=renderer.createRenderRequest().setWaitForPresent(true);
                    boolean finish="true".equals(args.getString("finish"));
                    boolean inspect="true".equals(args.getString("inspect"));
                    java.util.concurrent.CountDownLatch commit=new java.util.concurrent.CountDownLatch(1);
                    java.util.concurrent.atomic.AtomicReference<String> commitContext=new java.util.concurrent.atomic.AtomicReference<>();
                    java.util.concurrent.atomic.AtomicInteger commitError=new java.util.concurrent.atomic.AtomicInteger(-1);
                    java.util.concurrent.atomic.AtomicReference<JSONObject> frameState=new java.util.concurrent.atomic.AtomicReference<>();
                    if(finish||inspect)request.setFrameCommitCallback(Runnable::run,()->{
                        try {commitContext.set(GLES20.glGetString(GLES20.GL_VERSION));
                            if(commitContext.get()!=null){
                                if(finish)GLES20.glFinish();
                                if(inspect) {
                                    JSONObject state=new JSONObject();int[] v=new int[1];
                                    GLES20.glGetIntegerv(GLES20.GL_CURRENT_PROGRAM,v,0);int program=v[0];
                                    state.put("program",program).put("position_location",GLES20.glGetAttribLocation(program,"position"))
                                        .put("color_location",GLES20.glGetAttribLocation(program,"color"));
                                    for(int parameter:new int[]{0x80c9,0x80c8,0x80cb,0x80ca,0x8009,0x883d}) {
                                        GLES20.glGetIntegerv(parameter,v,0);state.put("gl_"+Integer.toHexString(parameter),v[0]);
                                    }
                                    state.put("blend",GLES20.glIsEnabled(GLES20.GL_BLEND));
                                    java.nio.ByteBuffer buffer=java.nio.ByteBuffer.allocateDirect(width*height*4);
                                    GLES20.glReadPixels(0,0,width,height,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,buffer);
                                    state.put("current_framebuffer",colors(buffer,width,height,width*4,4));frameState.set(state);
                                }
                                commitError.set(GLES20.glGetError());}}
                        catch(Exception exception){try{frameState.set(new JSONObject().put("error",exception.toString()));}catch(Exception ignored){}}
                        finally{commit.countDown();}
                    });
                    result.put("draw_result",request.syncAndDraw());
                    if(finish||inspect)result.put("finish_callback_ran",commit.await(5,java.util.concurrent.TimeUnit.SECONDS))
                        .put("finish_callback_context",commitContext.get()).put("finish_callback_gl_error",commitError.get())
                        .put("frame_state",frameState.get());
                    for(int retry=0;retry<30&&image==null;retry++){image=reader.acquireLatestImage();if(image==null)SystemClock.sleep(100);}
                    if(image==null)throw new IllegalStateException("HWUI did not publish an image");
                    Image.Plane plane=image.getPlanes()[0];java.nio.ByteBuffer pixels=plane.getBuffer();
                    JSONArray samples=new JSONArray();
                    for(int x:new int[]{width/4,3*width/4}){
                        int offset=(height/2)*plane.getRowStride()+x*plane.getPixelStride();JSONArray rgba=new JSONArray();
                        for(int channel=0;channel<4;channel++)rgba.put(pixels.get(offset+channel)&255);samples.put(rgba);
                    }
                    result.put("samples_rgba",samples).put("row_stride",plane.getRowStride())
                          .put("pixel_stride",plane.getPixelStride()).put("target_size",width+"x"+height)
                          .put("production_window_policy_changed",false);
                    int red=0,green=0,other=0;
                    for(int y=0;y<height;y++)for(int x=0;x<width;x++) {
                        int pos=y*plane.getRowStride()+x*plane.getPixelStride();
                        int r=pixels.get(pos)&255,g=pixels.get(pos+1)&255,b=pixels.get(pos+2)&255;
                        if(r==255&&g==0&&b==0)red++;
                        else if(r==0&&g==255&&b==0)green++;
                        else other++;
                    }
                    result.put("red_pixels",red).put("green_pixels",green).put("other_pixels",other)
                          .put("color_counts_match",red==width*height/2&&green==width*height/2&&other==0);
                } finally {if(image!=null)image.close();renderer.destroy();reader.close();}
            } else if("https".equals(action)) {
                ConnectivityManager cm=getTargetContext().getSystemService(ConnectivityManager.class);
                Network net=cm.getActiveNetwork();NetworkCapabilities nc=cm.getNetworkCapabilities(net);
                LinkProperties lp=cm.getLinkProperties(net);
                result.put("wifi_transport",nc!=null&&nc.hasTransport(NetworkCapabilities.TRANSPORT_WIFI));
                result.put("validated",nc!=null&&nc.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED));
                result.put("dns_count",lp==null?0:lp.getDnsServers().size());
                boolean defaultRoute=false;if(lp!=null)for(RouteInfo route:lp.getRoutes())defaultRoute|=route.isDefaultRoute();
                result.put("default_route",defaultRoute);
                long start=SystemClock.elapsedRealtime();
                result.put("dns_result_count",InetAddress.getAllByName("connectivitycheck.gstatic.com").length);
                HttpsURLConnection c=(HttpsURLConnection)new URL("https://connectivitycheck.gstatic.com/generate_204").openConnection();
                c.setConnectTimeout(15000);c.setReadTimeout(15000);c.setInstanceFollowRedirects(false);
                try {result.put("https_code",c.getResponseCode());result.put("tls_cipher",c.getCipherSuite());}
                finally {c.disconnect();}
                result.put("elapsed_ms",SystemClock.elapsedRealtime()-start);
            } else {
                UiAutomation ui=getUiAutomation();
                if("tap".equals(action)) {
                    float x=Float.parseFloat(args.getString("x")),y=Float.parseFloat(args.getString("y"));
                    long t=SystemClock.uptimeMillis();
                    MotionEvent down=MotionEvent.obtain(t,t,MotionEvent.ACTION_DOWN,x,y,0);down.setSource(InputDevice.SOURCE_TOUCHSCREEN);
                    java.lang.reflect.Method inject=UiAutomation.class.getDeclaredMethod(
                            "injectInputEvent",android.view.InputEvent.class,boolean.class,boolean.class);
                    long beforeDown=SystemClock.elapsedRealtime();
                    boolean d=(Boolean)inject.invoke(ui,down,false,false);
                    long downDuration=SystemClock.elapsedRealtime()-beforeDown;SystemClock.sleep(40);
                    MotionEvent up=MotionEvent.obtain(t,t+40,MotionEvent.ACTION_UP,x,y,0);up.setSource(InputDevice.SOURCE_TOUCHSCREEN);
                    long beforeUp=SystemClock.elapsedRealtime();
                    boolean u=(Boolean)inject.invoke(ui,up,false,false);
                    long upDuration=SystemClock.elapsedRealtime()-beforeUp;down.recycle();up.recycle();
                    result.put("injected",d&&u).put("duration_ms",40).put("synchronous_dispatch",false)
                          .put("wait_for_animations",false).put("down_call_ms",downDuration)
                          .put("up_call_ms",upDuration);
                } else {
                    JSONArray nodes=new JSONArray();List<AccessibilityNodeInfo> found=new ArrayList<>();
                    String target=args.getString("target");visit(root(ui),nodes,target,found);
                    result.put("nodes",nodes);
                    if("click".equals(action)) {
                        if(found.size()!=1)throw new IllegalStateException("Exact target match count="+found.size());
                        AccessibilityNodeInfo n=found.get(0);
                        while(n!=null&&!n.isClickable())n=n.getParent();
                        if(n==null||!n.isEnabled())throw new IllegalStateException("Target has no enabled clickable ancestor");
                        result.put("clicked",n.performAction(AccessibilityNodeInfo.ACTION_CLICK));
                    }
                }
            }
            result.put("completed",true);
        } catch(Throwable ex) {
            try {result.put("completed",false).put("error",ex.getClass().getName()+": "+ex.getMessage());}catch(Exception ignored){}
        }
        Bundle out=new Bundle();out.putString("report",result.toString());finish(0,out);
    }
}
