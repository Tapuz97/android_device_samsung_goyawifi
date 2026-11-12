import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Looper;
import android.view.Surface;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;

/** Transient surface; compares CPU Canvas and actual HWUI on the current boot. */
public class T110CanvasProbe {
    private static Object invoke(Object o, String name, Class<?>[] types, Object... args) throws Exception {
        Method m=o.getClass().getDeclaredMethod(name,types);m.setAccessible(true);return m.invoke(o,args);
    }
    public static void main(String[] args) throws Exception {
        System.setOut(new java.io.PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.out),true));
        boolean hardware=args[0].equals("hardware");
        int w=Integer.parseInt(args[1]),h=Integer.parseInt(args[2]);
        if ((w!=600 && w!=1024) || (h!=600 && h!=1024)) throw new IllegalArgumentException();
        Looper.prepareMainLooper();
        Class<?> scClass=Class.forName("android.view.SurfaceControl");
        Class<?> builderClass=Class.forName("android.view.SurfaceControl$Builder");
        Constructor<?> bc=builderClass.getDeclaredConstructor();bc.setAccessible(true);Object builder=bc.newInstance();
        invoke(builder,"setName",new Class<?>[]{String.class},"T110 Canvas comparison");
        invoke(builder,"setBufferSize",new Class<?>[]{int.class,int.class},w,h);
        invoke(builder,"setFormat",new Class<?>[]{int.class},1);
        Object sc=invoke(builder,"build",new Class<?>[]{});
        Class<?> txClass=Class.forName("android.view.SurfaceControl$Transaction");
        Constructor<?> tc=txClass.getDeclaredConstructor();tc.setAccessible(true);Object tx=tc.newInstance();
        Constructor<Surface> constructor=Surface.class.getDeclaredConstructor(scClass);constructor.setAccessible(true);
        Surface surface=constructor.newInstance(sc);
        try {
            invoke(tx,"setLayerStack",new Class<?>[]{scClass,int.class},sc,0);
            invoke(tx,"setLayer",new Class<?>[]{scClass,int.class},sc,2147483600);
            invoke(tx,"show",new Class<?>[]{scClass},sc);
            invoke(tx,"apply",new Class<?>[]{});
            Canvas canvas=hardware?surface.lockHardwareCanvas():surface.lockCanvas(null);
            Paint paint=new Paint();
            canvas.drawColor(Color.rgb(32,32,32));
            int[] colors={Color.RED,Color.GREEN,Color.BLUE,Color.WHITE};
            for(int i=0;i<4;i++) {paint.setColor(colors[i]);canvas.drawRect((i%2)*w/2f,(i/2)*h/2f,(i%2+1)*w/2f,(i/2+1)*h/2f,paint);}
            Bitmap bitmap=Bitmap.createBitmap(128,128,Bitmap.Config.ARGB_8888);
            for(int y=0;y<128;y++)for(int x=0;x<128;x++)bitmap.setPixel(x,y,Color.rgb(x*2,y*2,128));
            canvas.drawBitmap(bitmap,w/2f-64,h/2f-64,paint);
            paint.setColor(Color.BLACK);paint.setAntiAlias(true);
            canvas.drawCircle(48,48,24,paint);
            surface.unlockCanvasAndPost(canvas);
            System.out.println("CANVAS_POSTED "+(hardware?"hardware":"software")+" "+w+"x"+h);System.out.flush();
            // HWUI/BLAST posts its buffer transaction back to this looper.
            // Sleeping here prevents a GPU frame from ever reaching SurfaceFlinger.
            new android.os.Handler(Looper.myLooper()).postDelayed(() -> Looper.myLooper().quitSafely(),14000);
            Looper.loop();
        } finally {
            invoke(tx,"remove",new Class<?>[]{scClass},sc);invoke(tx,"apply",new Class<?>[]{});
            surface.release();invoke(tx,"close",new Class<?>[]{});invoke(sc,"release",new Class<?>[]{});
        }
        System.out.println("CANVAS_REMOVED");System.out.flush();System.exit(0);
    }
}
