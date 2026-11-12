import android.graphics.*;
import android.media.Image;
import android.media.ImageReader;
import android.os.*;
import android.view.Surface;
import java.io.*;
import java.lang.reflect.*;

/** Same HWUI frame with/without CPU-readable storage, handed directly to SF. */
public class T110BufferDisplay {
    static Object invoke(Object o,String n,Class<?>[] types,Object... args)throws Exception{
        Method m=o.getClass().getDeclaredMethod(n,types);m.setAccessible(true);return m.invoke(o,args);
    }
    public static void main(String[] args)throws Exception{
        System.setOut(new PrintStream(new FileOutputStream(FileDescriptor.out),true));
        long usage=Long.decode(args[0]);
        Looper.prepareMainLooper();Handler h=new Handler(Looper.myLooper());
        ImageReader reader=ImageReader.newInstance(600,1024,PixelFormat.RGBA_8888,3,usage);
        Surface surface=reader.getSurface();
        reader.setOnImageAvailableListener(r->{
            try{
                Image img=r.acquireLatestImage();if(img==null)return;
                android.hardware.HardwareBuffer buffer=img.getHardwareBuffer();
                Class<?> scClass=Class.forName("android.view.SurfaceControl");
                Constructor<?> bc=Class.forName("android.view.SurfaceControl$Builder").getDeclaredConstructor();bc.setAccessible(true);
                Object builder=bc.newInstance();
                invoke(builder,"setName",new Class<?>[]{String.class},"T110 buffer usage comparison");
                invoke(builder,"setBufferSize",new Class<?>[]{int.class,int.class},600,1024);
                Object sc=invoke(builder,"build",new Class<?>[]{});
                Constructor<?> tc=Class.forName("android.view.SurfaceControl$Transaction").getDeclaredConstructor();tc.setAccessible(true);Object tx=tc.newInstance();
                invoke(tx,"setLayerStack",new Class<?>[]{scClass,int.class},sc,0);
                invoke(tx,"setLayer",new Class<?>[]{scClass,int.class},sc,2000000);
                invoke(tx,"setBuffer",new Class<?>[]{scClass,android.hardware.HardwareBuffer.class},sc,buffer);
                invoke(tx,"show",new Class<?>[]{scClass},sc);invoke(tx,"apply",new Class<?>[]{});
                System.out.println("BUFFER_POSTED usage="+buffer.getUsage());
                h.postDelayed(()->{
                    try{invoke(tx,"remove",new Class<?>[]{scClass},sc);invoke(tx,"apply",new Class<?>[]{});
                        buffer.close();img.close();surface.release();reader.close();
                        invoke(tx,"close",new Class<?>[]{});invoke(sc,"release",new Class<?>[]{});
                    }catch(Exception e){e.printStackTrace();System.exit(2);}
                    System.out.println("BUFFER_REMOVED");System.exit(0);
                },12000);
            }catch(Exception e){e.printStackTrace();System.exit(2);}
        },h);
        h.postDelayed(()->System.exit(3),25000);
        Canvas canvas=surface.lockHardwareCanvas();Paint p=new Paint();
        canvas.drawColor(Color.BLACK);
        int[] colors={Color.RED,Color.GREEN,Color.BLUE,Color.WHITE};
        for(int i=0;i<4;i++){p.setColor(colors[i]);canvas.drawRect(i%2*300,i/2*512,(i%2+1)*300,(i/2+1)*512,p);}
        p.setColor(Color.BLACK);p.setAntiAlias(true);canvas.drawCircle(48,48,24,p);
        surface.unlockCanvasAndPost(canvas);Looper.loop();
    }
}
