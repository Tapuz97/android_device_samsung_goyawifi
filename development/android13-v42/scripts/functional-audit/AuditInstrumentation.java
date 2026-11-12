package dev.tapuz.t110.audit;

import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.hardware.*;
import android.hardware.camera2.CameraManager;
import android.location.LocationManager;
import android.media.MediaCodecList;
import android.media.MediaCodec;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import android.appwidget.*;
import android.provider.*;
import android.database.Cursor;
import android.net.*;
import android.net.wifi.WifiManager;
import android.os.*;
import android.security.keystore.*;
import android.webkit.*;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.*;
import java.util.concurrent.*;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;

/** No ROM changes: API tests execute as an ordinary, unprivileged application. */
public class AuditInstrumentation extends Instrumentation {
    Context context;AuditActivity activity;JSONObject report=new JSONObject();JSONArray results=new JSONArray();
    boolean codecsOnly;
    interface Check {JSONObject run() throws Exception;}
    JSONObject result(String status,String detail) throws Exception {return new JSONObject().put("status",status).put("detail",detail);}
    void save() throws Exception {
        report.put("results",results);
        try(FileOutputStream out=context.openFileOutput("report.json",Context.MODE_PRIVATE)) {
            out.write(report.toString(2).getBytes(StandardCharsets.UTF_8));
        }
    }
    void check(String id,Check action) throws Exception {
        if(codecsOnly && !id.equals("app-start") && !id.equals("codec-inventory") && !id.endsWith("-decode"))return;
        report.put("running",id);save();long start=SystemClock.elapsedRealtime();JSONObject row;
        try {row=action.run();}catch(Throwable t) {row=result("FAIL",t.getClass().getName()+": "+t.getMessage());}
        row.put("id",id).put("elapsed_ms",SystemClock.elapsedRealtime()-start);
        results.put(row);report.put("running",JSONObject.NULL);save();
        Bundle state=new Bundle();state.putString("stream",id+" "+row.getString("status")+"\n");sendStatus(0,state);
    }
    @Override public void onCreate(Bundle args) {super.onCreate(args);codecsOnly=args!=null&&"true".equals(args.getString("codecsOnly"));start();}
    @Override public void onStart() {
        context=getTargetContext();
        try {
            report.put("uid",android.os.Process.myUid()).put("sdk",Build.VERSION.SDK_INT).put("mode",codecsOnly?"CODEC_REGRESSION_ONLY":"API_AUDIT_NO_FIXES");save();
            Intent intent=new Intent(context,AuditActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            activity=(AuditActivity)startActivitySync(intent);
            check("app-start",()->result("PASS","Normal application Activity launched"));
            check("private-storage",()->fileRoundtrip(context.getFilesDir()));
            check("shared-app-storage",()->fileRoundtrip(context.getExternalFilesDir(null)));
            check("keystore-aes",()->{
                String alias="t110-audit-"+UUID.randomUUID();KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);
                try {
                    KeyGenerator gen=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
                    gen.init(new KeyGenParameterSpec.Builder(alias,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT)
                        .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).setKeySize(256).build());
                    SecretKey key=gen.generateKey();byte[] plain="T110-functional-audit".getBytes(StandardCharsets.UTF_8);
                    Cipher enc=Cipher.getInstance("AES/GCM/NoPadding");enc.init(Cipher.ENCRYPT_MODE,key);byte[] encrypted=enc.doFinal(plain);
                    Cipher dec=Cipher.getInstance("AES/GCM/NoPadding");dec.init(Cipher.DECRYPT_MODE,key,new GCMParameterSpec(128,enc.getIV()));
                    if(!Arrays.equals(plain,dec.doFinal(encrypted)))throw new AssertionError("AES data mismatch");
                    KeyInfo info=(KeyInfo)SecretKeyFactory.getInstance(key.getAlgorithm(),"AndroidKeyStore").getKeySpec(key,KeyInfo.class);
                    return result("PASS","AES-256 GCM key generation and encrypt/decrypt").put("hardware_backed",info.isInsideSecureHardware());
                }finally{if(ks.containsAlias(alias))ks.deleteEntry(alias);}
            });
            check("clipboard",()->{
                final Throwable[] error=new Throwable[1];
                runOnMainSync(()->{try{
                    android.content.ClipboardManager cm=context.getSystemService(android.content.ClipboardManager.class);
                    ClipData prior=cm.getPrimaryClip();boolean hadPrior=prior!=null;
                    try{cm.setPrimaryClip(ClipData.newPlainText("audit","T110-audit"));
                        if(cm.getPrimaryClip()==null||!"T110-audit".contentEquals(cm.getPrimaryClip().getItemAt(0).coerceToText(context)))throw new AssertionError("Clipboard roundtrip failed");
                    }finally{if(hadPrior)cm.setPrimaryClip(prior);else cm.clearPrimaryClip();}
                }catch(Throwable t){error[0]=t;}});
                if(error[0]!=null)throw new Exception(error[0]);return result("PASS","Foreground copy/paste; prior clipboard restored without logging it");
            });
            check("notifications",()->{
                NotificationManager nm=context.getSystemService(NotificationManager.class);
                if(!nm.areNotificationsEnabled())return result("BLOCKED","QA notification permission not granted");
                String channel="t110-functional-audit";nm.createNotificationChannel(new NotificationChannel(channel,"Functional audit",NotificationManager.IMPORTANCE_LOW));
                try{nm.notify(8151,new Notification.Builder(context,channel).setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle("Functional audit").setContentText("Temporary notification delivery check").build());
                    if(nm.getActiveNotifications().length==0)throw new AssertionError("Notification not active");
                    return result("PASS","Ordinary app notification posted and visible to NotificationManager");
                }finally{nm.cancel(8151);nm.deleteNotificationChannel(channel);}
            });
            check("alarm-delivery",()->{
                AlarmManager am=context.getSystemService(AlarmManager.class);
                if(!am.canScheduleExactAlarms())return result("BLOCKED","Exact-alarm permission unavailable to QA package");
                AuditAlarmReceiver.delivered=new CountDownLatch(1);
                PendingIntent pi=PendingIntent.getBroadcast(context,8152,new Intent(context,AuditAlarmReceiver.class),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
                long due=SystemClock.elapsedRealtime()+2500;
                try{am.setExact(AlarmManager.ELAPSED_REALTIME_WAKEUP,due,pi);
                    if(!AuditAlarmReceiver.delivered.await(15,TimeUnit.SECONDS))throw new AssertionError("No alarm broadcast within 15 seconds");
                    return result("PASS","Exact elapsed-realtime wakeup alarm delivered to an app receiver").put("lateness_ms",AuditAlarmReceiver.receivedAt-due);
                }finally{am.cancel(pi);pi.cancel();AuditAlarmReceiver.delivered=null;}
            });
            check("camera-enumeration",()->{
                String[] ids=context.getSystemService(CameraManager.class).getCameraIdList();
                return result(ids.length>0?"PARTIAL":"FAIL","Camera IDs enumerated, not preview/capture validation").put("camera_count",ids.length);
            });
            check("accelerometer",()->{
                SensorManager sm=context.getSystemService(SensorManager.class);List<Sensor> all=sm.getSensorList(Sensor.TYPE_ALL);
                Sensor accel=sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
                if(accel==null)return result("FAIL","No Android accelerometer although kernel exposes a physical accelerometer input").put("sensor_count",all.size());
                CountDownLatch latch=new CountDownLatch(1);SensorEventListener listener=new SensorEventListener(){public void onAccuracyChanged(Sensor s,int a){}public void onSensorChanged(SensorEvent ev){latch.countDown();}};
                try{sm.registerListener(listener,accel,SensorManager.SENSOR_DELAY_NORMAL);
                    return result(latch.await(5,TimeUnit.SECONDS)?"PASS":"FAIL","Accelerometer event delivery").put("sensor_count",all.size());
                }finally{sm.unregisterListener(listener);}
            });
            check("hardware-capabilities",()->{
                JSONObject r=result("INVENTORY_ONLY","Declarations/availability are not operational passes");
                PackageManager pm=context.getPackageManager();
                for(String f:new String[]{PackageManager.FEATURE_CAMERA,PackageManager.FEATURE_CAMERA_FRONT,PackageManager.FEATURE_CAMERA_FLASH,PackageManager.FEATURE_WIFI,PackageManager.FEATURE_BLUETOOTH,PackageManager.FEATURE_LOCATION_GPS,PackageManager.FEATURE_SENSOR_ACCELEROMETER,PackageManager.FEATURE_NFC,PackageManager.FEATURE_TELEPHONY})r.put(f,pm.hasSystemFeature(f));
                r.put("wifi_state",context.getSystemService(WifiManager.class).getWifiState());
                r.put("location_providers",new JSONArray(context.getSystemService(LocationManager.class).getAllProviders()));
                r.put("vibrator_reported",context.getSystemService(Vibrator.class).hasVibrator());return r;
            });
            check("codec-inventory",()->{
                JSONArray names=new JSONArray();for(android.media.MediaCodecInfo info:new MediaCodecList(MediaCodecList.ALL_CODECS).getCodecInfos())names.put(info.getName());
                return result("INVENTORY_ONLY","Codec enumeration is not decode/encode validation").put("codecs",names);
            });
            check("storage-environment",()->{
                JSONArray volumes=new JSONArray();
                for(android.os.storage.StorageVolume v:context.getSystemService(android.os.storage.StorageManager.class).getStorageVolumes())volumes.put(new JSONObject().put("state",v.getState()).put("primary",v.isPrimary()).put("emulated",v.isEmulated()).put("directory",String.valueOf(v.getDirectory())));
                return result("INVENTORY_ONLY","Storage view from ordinary app UID").put("state",Environment.getExternalStorageState()).put("external_dir",String.valueOf(context.getExternalFilesDir(null))).put("storage_volumes",volumes);
            });
            check("contacts-crud",()->{
                ContentResolver cr=context.getContentResolver();android.net.Uri raw=null;
                try{
                    ContentValues v=new ContentValues();v.putNull(ContactsContract.RawContacts.ACCOUNT_NAME);v.putNull(ContactsContract.RawContacts.ACCOUNT_TYPE);
                    raw=cr.insert(ContactsContract.RawContacts.CONTENT_URI,v);if(raw==null)throw new IOException("No raw contact URI");
                    ContentValues data=new ContentValues();data.put(ContactsContract.Data.RAW_CONTACT_ID,ContentUris.parseId(raw));data.put(ContactsContract.Data.MIMETYPE,ContactsContract.CommonDataKinds.StructuredName.CONTENT_ITEM_TYPE);data.put(ContactsContract.CommonDataKinds.StructuredName.DISPLAY_NAME,"T110 temporary QA "+UUID.randomUUID());
                    if(cr.insert(ContactsContract.Data.CONTENT_URI,data)==null)throw new IOException("No contact data URI");
                    try(Cursor c=cr.query(raw,new String[]{"_id"},null,null,null)){if(c==null||!c.moveToFirst())throw new IOException("Own test contact not readable");}
                    return result("PASS","Own temporary local contact created/read; removed in cleanup. Existing contacts not queried.");
                }finally{if(raw!=null)cr.delete(raw,null,null);}
            });
            check("calendar-crud",()->{
                ContentResolver cr=context.getContentResolver();android.net.Uri calendar=null;String name="T110-QA-"+UUID.randomUUID();
                try{
                    android.net.Uri target=CalendarContract.Calendars.CONTENT_URI.buildUpon().appendQueryParameter(CalendarContract.CALLER_IS_SYNCADAPTER,"true").appendQueryParameter(CalendarContract.Calendars.ACCOUNT_NAME,name).appendQueryParameter(CalendarContract.Calendars.ACCOUNT_TYPE,CalendarContract.ACCOUNT_TYPE_LOCAL).build();
                    ContentValues v=new ContentValues();v.put(CalendarContract.Calendars.ACCOUNT_NAME,name);v.put(CalendarContract.Calendars.ACCOUNT_TYPE,CalendarContract.ACCOUNT_TYPE_LOCAL);v.put(CalendarContract.Calendars.NAME,name);v.put(CalendarContract.Calendars.CALENDAR_DISPLAY_NAME,name);v.put(CalendarContract.Calendars.CALENDAR_COLOR,0xff008080);v.put(CalendarContract.Calendars.CALENDAR_ACCESS_LEVEL,CalendarContract.Calendars.CAL_ACCESS_OWNER);v.put(CalendarContract.Calendars.OWNER_ACCOUNT,name);v.put(CalendarContract.Calendars.CALENDAR_TIME_ZONE,"UTC");v.put(CalendarContract.Calendars.SYNC_EVENTS,0);
                    calendar=cr.insert(target,v);if(calendar==null)throw new IOException("No local QA calendar URI");
                    ContentValues event=new ContentValues();event.put(CalendarContract.Events.CALENDAR_ID,ContentUris.parseId(calendar));event.put(CalendarContract.Events.TITLE,"Temporary functional check");event.put(CalendarContract.Events.DTSTART,System.currentTimeMillis()+3600000);event.put(CalendarContract.Events.DTEND,System.currentTimeMillis()+3660000);event.put(CalendarContract.Events.EVENT_TIMEZONE,"UTC");event.put(CalendarContract.Events.HAS_ALARM,0);
                    android.net.Uri uri=cr.insert(CalendarContract.Events.CONTENT_URI,event);if(uri==null)throw new IOException("No event URI");
                    try(Cursor c=cr.query(uri,new String[]{"_id"},null,null,null)){if(c==null||!c.moveToFirst())throw new IOException("Own QA event unreadable");}
                    return result("PASS","Own local calendar and event created/read; calendar/event removed in cleanup. No sync account configured.");
                }finally{if(calendar!=null)cr.delete(calendar,null,null);}
            });
            check("mediastore-crud",()->{
                ContentResolver cr=context.getContentResolver();android.net.Uri uri=null;
                try{
                    ContentValues v=new ContentValues();v.put(MediaStore.MediaColumns.DISPLAY_NAME,"T110-QA-"+UUID.randomUUID()+".png");v.put(MediaStore.MediaColumns.MIME_TYPE,"image/png");v.put(MediaStore.MediaColumns.RELATIVE_PATH,"Pictures/T110-QA");
                    uri=cr.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI,v);if(uri==null)throw new IOException("No MediaStore URI");
                    android.graphics.Bitmap bmp=android.graphics.Bitmap.createBitmap(4,4,android.graphics.Bitmap.Config.ARGB_8888);bmp.eraseColor(0xff008080);
                    try(OutputStream out=cr.openOutputStream(uri)){if(out==null||!bmp.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out))throw new IOException("MediaStore image write failed");}finally{bmp.recycle();}
                    try(InputStream in=cr.openInputStream(uri)){if(in==null||in.read()!=137)throw new IOException("MediaStore image not readable PNG");}
                    return result("PASS","Own temporary MediaStore PNG written/read through provider, then removed");
                }finally{if(uri!=null)cr.delete(uri,null,null);}
            });
            check("widget-host",()->{
                AppWidgetManager manager=AppWidgetManager.getInstance(context);AppWidgetProviderInfo provider=null;
                for(AppWidgetProviderInfo info:manager.getInstalledProviders())if(info.provider.getPackageName().equals("com.android.deskclock")){provider=info;break;}
                if(provider==null)return result("BLOCKED","No DeskClock widget provider installed");
                java.util.concurrent.atomic.AtomicInteger updates=new java.util.concurrent.atomic.AtomicInteger();
                AppWidgetHost host=new AppWidgetHost(context,8153){@Override protected AppWidgetHostView onCreateView(Context c,int id,AppWidgetProviderInfo info){return new AppWidgetHostView(c){@Override public void updateAppWidget(android.widget.RemoteViews views){super.updateAppWidget(views);if(views!=null)updates.incrementAndGet();}};}};
                int id=host.allocateAppWidgetId();final AppWidgetProviderInfo chosen=provider;
                try{
                    if(!manager.bindAppWidgetIdIfAllowed(id,provider.provider))return result("BLOCKED","QA widget-bind permission not granted");
                    host.startListening();final AppWidgetHostView[] view={null};
                    runOnMainSync(()->{view[0]=host.createView(activity,id,chosen);activity.setContentView(view[0]);});
                    long deadline=SystemClock.elapsedRealtime()+8000;while(updates.get()==0&&SystemClock.elapsedRealtime()<deadline)SystemClock.sleep(100);
                    if(manager.getAppWidgetInfo(id)==null||updates.get()==0)throw new IOException("No bound widget update delivered");
                    return result("PASS","DeskClock widget bound and RemoteViews update delivered to QA host; launcher layout unchanged").put("provider",provider.provider.flattenToShortString()).put("updates",updates.get());
                }finally{host.stopListening();host.deleteHost();}
            });
            check("h264-software-decode",()->decode("audit-video.mp4","video/"));
            check("aac-software-decode",()->decode("audit-audio.m4a","audio/"));
            check("h264-omx-decode",()->decode("audit-video.mp4","video/","OMX.google.h264.decoder"));
            check("aac-omx-decode",()->decode("audit-audio.m4a","audio/","OMX.google.aac.decoder"));
            check("webview-render-js",()->{
                CountDownLatch done=new CountDownLatch(1);String[] answer={null};Throwable[] error={null};WebView[] web={null};
                runOnMainSync(()->{try{
                    WebView view=new WebView(activity);web[0]=view;activity.setContentView(view);view.getSettings().setJavaScriptEnabled(true);
                    view.setWebViewClient(new WebViewClient(){@Override public void onPageFinished(WebView v,String url){v.evaluateJavascript("document.getElementById('probe').textContent",s->{answer[0]=s;done.countDown();});}});
                    view.loadDataWithBaseURL("https://audit.invalid/","<html><body><div id='probe'>T110-rendered</div></body></html>","text/html","UTF-8",null);
                }catch(Throwable t){error[0]=t;done.countDown();}});
                try{if(!done.await(30,TimeUnit.SECONDS))throw new AssertionError("WebView did not finish local HTML/JS in 30 seconds");
                    if(error[0]!=null)throw new Exception(error[0]);
                    if(!"\"T110-rendered\"".equals(answer[0]))throw new AssertionError("WebView JavaScript result "+answer[0]);
                    return result("PASS","Local HTML load and JavaScript DOM query completed; no internet requested");
                }finally{runOnMainSync(()->{if(web[0]!=null)web[0].destroy();});}
            });
            report.put("completed",true);save();
            runOnMainSync(()->activity.finish());Bundle b=new Bundle();b.putString("stream",report.toString(2)+"\n");finish(Activity.RESULT_OK,b);
        }catch(Throwable t){try{report.put("fatal",t.toString());save();}catch(Exception ignored){}Bundle b=new Bundle();b.putString("stream",t.toString());finish(Activity.RESULT_CANCELED,b);}
    }
    JSONObject fileRoundtrip(File dir) throws Exception {
        if(dir==null)throw new IOException("App storage directory unavailable");
        File f=new File(dir,"t110-audit-"+UUID.randomUUID());byte[] bytes=new byte[16384];new SecureRandom().nextBytes(bytes);
        try{try(FileOutputStream out=new FileOutputStream(f)){out.write(bytes);out.getFD().sync();}
            byte[] read=new byte[bytes.length];try(FileInputStream in=new FileInputStream(f)){int n=0,k;while(n<read.length&&(k=in.read(read,n,read.length-n))>0)n+=k;if(n!=bytes.length)throw new IOException("Short file read");}
            if(!Arrays.equals(bytes,read))throw new AssertionError("File roundtrip mismatch");
            return result("PASS","16384-byte random file write/fsync/read matched in ordinary app sandbox");
        }finally{if(f.exists()&&!f.delete())throw new IOException("Cannot delete own QA test file");}
    }
    JSONObject decode(String asset,String prefix) throws Exception {
        return decode(asset,prefix,null);
    }
    JSONObject decode(String asset,String prefix,String explicitDecoder) throws Exception {
        File file=new File(context.getCacheDir(),asset);MediaExtractor extractor=new MediaExtractor();MediaCodec codec=null;
        try{
            try(InputStream in=context.getAssets().open(asset);OutputStream out=new FileOutputStream(file)){byte[] b=new byte[4096];int n;while((n=in.read(b))>0)out.write(b,0,n);}
            extractor.setDataSource(file.getAbsolutePath());int track=-1;MediaFormat format=null;
            for(int i=0;i<extractor.getTrackCount();i++){MediaFormat f=extractor.getTrackFormat(i);if(f.getString(MediaFormat.KEY_MIME).startsWith(prefix)){track=i;format=f;break;}}
            if(track<0)throw new IOException("No media track");extractor.selectTrack(track);
            codec=explicitDecoder==null?MediaCodec.createDecoderByType(format.getString(MediaFormat.KEY_MIME)):MediaCodec.createByCodecName(explicitDecoder);String decoder=codec.getName();codec.configure(format,null,null,0);codec.start();
            MediaCodec.BufferInfo info=new MediaCodec.BufferInfo();boolean inputDone=false,outputDone=false;int frames=0;long bytes=0,deadline=SystemClock.elapsedRealtime()+20000;
            while(!outputDone&&SystemClock.elapsedRealtime()<deadline){
                if(!inputDone){int index=codec.dequeueInputBuffer(10000);if(index>=0){java.nio.ByteBuffer buffer=codec.getInputBuffer(index);int size=extractor.readSampleData(buffer,0);if(size<0){codec.queueInputBuffer(index,0,0,0,MediaCodec.BUFFER_FLAG_END_OF_STREAM);inputDone=true;}else{codec.queueInputBuffer(index,0,size,extractor.getSampleTime(),0);extractor.advance();}}}
                int index=codec.dequeueOutputBuffer(info,10000);if(index>=0){if(info.size>0){frames++;bytes+=info.size;}outputDone=(info.flags&MediaCodec.BUFFER_FLAG_END_OF_STREAM)!=0;codec.releaseOutputBuffer(index,false);}
            }
            if(!outputDone||frames==0)throw new IOException("Decode incomplete: frames="+frames+" eos="+outputDone);
            return result("PASS","Software decode to buffers; no display/audio-output qualification").put("decoder",decoder).put("output_buffers",frames).put("decoded_bytes",bytes);
        }finally{if(codec!=null){try{codec.stop();}catch(Exception ignored){}codec.release();}extractor.release();if(file.exists())file.delete();}
    }
}
