import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Rect;
import android.graphics.Path;
import android.graphics.RectF;

/** Read-only offscreen pixel check for the notification row's clipping bounds. */
public class T110ClipProbe {
    private static int draw(boolean extreme, boolean rounded, int top, int height) {
        Bitmap b = Bitmap.createBitmap(600, 1024, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(b);
        if (rounded) {
            Path path = new Path();
            path.addRoundRect(new RectF(0,250,600,1024),
                new float[]{40,40,40,40,0,0,0,0},Path.Direction.CW);
            c.clipPath(path);
        } else c.clipRect(0, 250, 600, 1024);
        c.translate(20, top);
        c.clipRect(new Rect(extreme ? Integer.MIN_VALUE : -1024, 0,
                           extreme ? Integer.MAX_VALUE : 560 + 1024, height));
        android.graphics.Paint paint = new android.graphics.Paint();
        paint.setColor(Color.RED);
        c.drawRect(0, 0, 560, height, paint);
        int[] pixels = new int[600 * 1024];
        b.getPixels(pixels, 0, 600, 0, 0, 600, 1024);
        int count = 0;
        for (int pixel : pixels) if (pixel == Color.RED) count++;
        b.recycle();
        return count;
    }
    public static void main(String[] args) throws Exception {
        System.setOut(new java.io.PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.out), true));
        System.setErr(new java.io.PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.err), true));
        if (args.length > 0) {
            Class.forName("com.android.commands.content.Content").getMethod("main", String[].class)
                .invoke(null, (Object) args);
        } else {
            for (int[] geometry : new int[][] {{270,149}, {505,110}}) {
                for(boolean rounded : new boolean[]{false,true}) {
                    int finite = draw(false, rounded, geometry[0], geometry[1]);
                    if (finite != 560 * geometry[1]) throw new AssertionError("Finite clip lost row pixels");
                    System.out.println("CLIP rounded="+rounded+" top=" + geometry[0] + " height=" + geometry[1]
                        + " extreme=" + draw(true, rounded, geometry[0], geometry[1])
                        + " finite=" + finite
                        + " expected=" + (560 * geometry[1]));
                }
            }
            System.out.println("FINITE_NOTIFICATION_CLIP_PASS");
        }
        System.exit(0);
    }
}
