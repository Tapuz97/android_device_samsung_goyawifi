package dev.tapuz.t110.audit;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import java.util.concurrent.CountDownLatch;
public class AuditAlarmReceiver extends BroadcastReceiver {
    static volatile CountDownLatch delivered;
    static volatile long receivedAt;
    @Override public void onReceive(Context c,Intent i) {
        receivedAt=android.os.SystemClock.elapsedRealtime();
        CountDownLatch latch=delivered;if(latch!=null)latch.countDown();
    }
}
