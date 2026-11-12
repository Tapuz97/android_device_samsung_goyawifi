package dev.tapuz.t110.audit;
import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
public class AuditActivity extends Activity {
    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        TextView text=new TextView(this);
        text.setText("Functional audit in progress\n\nTemporary QA tool: checking normal app APIs.");
        text.setTextSize(20);text.setPadding(24,24,24,24);setContentView(text);
    }
}
