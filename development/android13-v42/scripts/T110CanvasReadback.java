import android.graphics.*;
import android.media.Image;
import android.media.ImageReader;
import android.hardware.HardwareBuffer;
import android.os.*;
import android.view.Surface;
import java.io.*;
import java.nio.ByteBuffer;

/** Offscreen HWUI comparison. No visible surfaces or device configuration writes. */
public class T110CanvasReadback {
    public static void main(String[] args) throws Exception {
        System.setOut(new PrintStream(new FileOutputStream(FileDescriptor.out),true));
        boolean hardware=args[0].equals("hardware");
        int w=Integer.parseInt(args[1]),h=Integer.parseInt(args[2]);
        String path=args[3];
        if (!path.startsWith("/data/local/tmp/t110-readback-")) throw new IllegalArgumentException();
        Looper.prepareMainLooper();
        Handler handler=new Handler(Looper.myLooper());
        ImageReader reader=ImageReader.newInstance(w,h,PixelFormat.RGBA_8888,3,
                HardwareBuffer.USAGE_GPU_COLOR_OUTPUT|HardwareBuffer.USAGE_CPU_READ_OFTEN);
        Surface surface=reader.getSurface();
        reader.setOnImageAvailableListener(r -> {
            try (Image img=r.acquireLatestImage()) {
                if(img==null)return;
                Image.Plane plane=img.getPlanes()[0];
                ByteBuffer b=plane.getBuffer();byte[] bytes=new byte[b.remaining()];b.get(bytes);
                try(FileOutputStream out=new FileOutputStream(path)) {out.write(bytes);}
                System.out.println("READBACK "+w+" "+h+" "+plane.getRowStride()+" "+plane.getPixelStride()+" "+bytes.length);
            } catch(Exception e) {e.printStackTrace();System.exit(2);}
            surface.release();reader.close();System.exit(0);
        },handler);
        handler.postDelayed(() -> {System.err.println("READBACK_TIMEOUT");System.exit(3);},20000);
        Canvas canvas=hardware?surface.lockHardwareCanvas():surface.lockCanvas(null);
        System.out.println("CANVAS_SIZE "+canvas.getWidth()+" "+canvas.getHeight()+" hardware="+canvas.isHardwareAccelerated());
        Paint p=new Paint();
        canvas.drawColor(Color.BLACK);
        int[] colors={Color.RED,Color.GREEN,Color.BLUE,Color.WHITE};
        for(int i=0;i<4;i++) {p.setColor(colors[i]);canvas.drawRect((i%2)*w/2f,(i/2)*h/2f,(i%2+1)*w/2f,(i/2+1)*h/2f,p);}
        Bitmap bitmap=Bitmap.createBitmap(128,128,Bitmap.Config.ARGB_8888);
        for(int y=0;y<128;y++)for(int x=0;x<128;x++)bitmap.setPixel(x,y,Color.rgb(x*2,y*2,128));
        canvas.drawBitmap(bitmap,w/2f-64,h/2f-64,p);
        p.setColor(Color.BLACK);p.setAntiAlias(true);canvas.drawCircle(48,48,24,p);
        surface.unlockCanvasAndPost(canvas);
        Looper.loop();
    }
}
