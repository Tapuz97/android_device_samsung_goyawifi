"""Verify actual transaction applier ordering and isolation of the software path."""
from pathlib import Path
import subprocess,json
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
root=p/'evidence/offline-v36/surface-transactions';root.mkdir(parents=True,exist_ok=True)
files={
'android/annotation/TargetApi.java':'package android.annotation; public @interface TargetApi { int value(); }',
'android/os/Build.java':'package android.os; public class Build { public static String DEVICE="t110_bringup"; public static class VERSION_CODES {public static final int R=30;} }',
'android/os/Handler.java':'''package android.os; import java.util.*; public class Handler { public interface Callback {boolean handleMessage(Message m);} public static final ArrayDeque<Runnable> queue=new ArrayDeque<>(); public Callback callback; public Handler(Callback c){callback=c;} public boolean post(Runnable r){queue.add(r);return true;} public static void drain(){while(!queue.isEmpty())queue.remove().run();}}''',
'android/os/Message.java':'''package android.os; public class Message {public int what,arg1,arg2;public Handler handler;public static Message obtain(Handler h,int w,int a,int b){Message m=new Message();m.handler=h;m.what=w;m.arg1=a;m.arg2=b;return m;}public void sendToTarget(){handler.post(()->handler.callback.handleMessage(this));}}''',
'android/util/Log.java':'package android.util; public class Log {public static int d(String a,String b){return 0;}}',
'android/view/SurfaceControl.java':'''package android.view;public class SurfaceControl {public boolean valid=true;public boolean isValid(){return valid;}public static class Transaction {public int applies;public void apply(){applies++;}}}''',
'android/view/View.java':'''package android.view;public class View {public interface OnAttachStateChangeListener{void onViewAttachedToWindow(View v);void onViewDetachedFromWindow(View v);} public ViewRootImpl root;public boolean hardware;public int invalidates;public ViewRootImpl getViewRootImpl(){return root;}public boolean isHardwareAccelerated(){return hardware;}public boolean isAttachedToWindow(){return root!=null;}public void invalidate(){invalidates++;}public void addOnAttachStateChangeListener(OnAttachStateChangeListener l){}public void removeOnAttachStateChangeListener(OnAttachStateChangeListener l){}}''',
'android/view/ViewRootImpl.java':'''package android.view;import java.util.*;import java.util.function.LongConsumer;public class ViewRootImpl {public View view;public SurfaceControl surface=new SurfaceControl();public List<LongConsumer> rt=new ArrayList<>();public View getView(){return view;}public SurfaceControl getSurfaceControl(){return surface;}public void registerRtFrameCallback(LongConsumer r){rt.add(r);}public void mergeWithNextTransaction(SurfaceControl.Transaction t,long frame){t.apply();}}''',
'com/android/quickstep/RemoteAnimationTargets.java':'''package com.android.quickstep;public class RemoteAnimationTargets{public static class ReleaseCheck {public boolean canRelease;public void setCanRelease(boolean b){canRelease=b;}}}''',
'com/android/quickstep/util/SurfaceTransaction.java':'''package com.android.quickstep.util;import android.view.SurfaceControl;public class SurfaceTransaction {public SurfaceControl.Transaction transaction=new SurfaceControl.Transaction();public SurfaceControl.Transaction getTransaction(){return transaction;}}''',
'com/android/quickstep/util/SoftwareSurfaceTest.java':'''package com.android.quickstep.util;import android.view.*;import android.os.*;
public class SoftwareSurfaceTest {
 static class F {View v=new View();ViewRootImpl r=new ViewRootImpl();SurfaceTransactionApplier a;F(){v.root=r;r.view=v;a=new SurfaceTransactionApplier(v);}}
 public static void main(String[] args){
  F f=new F();SurfaceTransaction x=new SurfaceTransaction(),y=new SurfaceTransaction();f.a.scheduleApply(x);f.a.scheduleApply(y);assert x.transaction.applies==1&&y.transaction.applies==1;assert f.r.rt.isEmpty();assert !f.a.canRelease;Handler.queue.remove().run();assert !f.a.canRelease;Handler.queue.remove().run();assert f.a.canRelease;assert f.v.invalidates==2;
  f=new F();f.r.surface.valid=false;x=new SurfaceTransaction();f.a.scheduleApply(x);Handler.drain();assert x.transaction.applies==0&&f.a.canRelease;
  f=new F();f.v.hardware=true;x=new SurfaceTransaction();f.a.scheduleApply(x);assert x.transaction.applies==0&&!f.a.canRelease;assert f.r.rt.size()==1;f.r.rt.get(0).accept(4L);Handler.drain();assert x.transaction.applies==1&&f.a.canRelease;
  Build.DEVICE="other";f=new F();x=new SurfaceTransaction();f.a.scheduleApply(x);assert f.r.rt.size()==1&&x.transaction.applies==0;f.r.rt.get(0).accept(5L);Handler.drain();assert f.a.canRelease;Build.DEVICE="t110_bringup";
  f=new F();f.r.view=null;x=new SurfaceTransaction();f.a.scheduleApply(x);assert x.transaction.applies==0&&f.a.canRelease&&Handler.queue.isEmpty();
  System.out.println("SOFTWARE_SURFACE_ORDERING_PASS: apply, ordered release, invalid surface, hardware and other-device paths, detach");
 }
}'''}
for name,text in files.items():
    dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text,encoding='utf-8')
src=Path('/root/t110-build/lineage20/packages/apps/Trebuchet/quickstep/src/com/android/quickstep/util/SurfaceTransactionApplier.java')
(root/'com/android/quickstep/util/SurfaceTransactionApplier.java').write_bytes(src.read_bytes())
jdk=Path('/root/t110-build/lineage20/prebuilts/jdk/jdk17/linux-x86/bin')
subprocess.run([str(jdk/'javac'),'-d',str(root/'classes')]+[str(f) for f in root.rglob('*.java')],check=True)
result=subprocess.check_output([str(jdk/'java'),'-ea','-cp',str(root/'classes'),'com.android.quickstep.util.SoftwareSurfaceTest'],text=True)
(root/'result.txt').write_text(result,encoding='utf-8');print(result)
