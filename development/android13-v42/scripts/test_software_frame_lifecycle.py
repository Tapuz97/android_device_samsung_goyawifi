"""Run the actual helper against deterministic draw/queue/surface lifecycle fixtures."""
from pathlib import Path
import subprocess,json
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
root=p/'evidence/offline-v36/frame-lifecycle';root.mkdir(parents=True,exist_ok=True)
files={
'android/os/Handler.java':'''package android.os; import java.util.ArrayDeque; public class Handler {
 public static final ArrayDeque<Runnable> queue=new ArrayDeque<>();
 public boolean post(Runnable r){queue.add(r);return true;}
 public static void drain(){while(!queue.isEmpty())queue.remove().run();}
}''',
'android/util/Log.java':'''package android.util; public class Log {public static int d(String a,String b){return 0;}}''',
'android/view/SurfaceControl.java':'''package android.view; public class SurfaceControl {public static class Transaction{}}''',
'android/view/ViewTreeObserver.java':'''package android.view; import java.util.*; public class ViewTreeObserver {
 public interface OnDrawListener{void onDraw();} public boolean alive=true,drawing=false;
 public final Set<OnDrawListener> listeners=new HashSet<>();
 public boolean isAlive(){return alive;}
 public void addOnDrawListener(OnDrawListener l){if(drawing)throw new AssertionError();listeners.add(l);}
 public void removeOnDrawListener(OnDrawListener l){if(drawing)throw new AssertionError("Removed inside draw");listeners.remove(l);}
 public void draw(){drawing=true;for(OnDrawListener l:new ArrayList<>(listeners))l.onDraw();drawing=false;}
}''',
'android/view/ViewRootImpl.java':'''package android.view; import java.util.*; public class ViewRootImpl {
 public interface SurfaceChangedCallback{void surfaceCreated(SurfaceControl.Transaction t);void surfaceReplaced(SurfaceControl.Transaction t);void surfaceDestroyed();}
 public View view; public final Set<SurfaceChangedCallback> callbacks=new HashSet<>();
 public View getView(){return view;} public void addSurfaceChangedCallback(SurfaceChangedCallback c){callbacks.add(c);}
 public void removeSurfaceChangedCallback(SurfaceChangedCallback c){callbacks.remove(c);}
 public void destroy(){for(SurfaceChangedCallback c:new ArrayList<>(callbacks))c.surfaceDestroyed();}
}''',
'android/view/View.java':'''package android.view; public class View {
 public ViewRootImpl root; public final ViewTreeObserver observer=new ViewTreeObserver(); public int invalidates;
 public ViewRootImpl getViewRootImpl(){return root;} public ViewTreeObserver getViewTreeObserver(){return observer;}
 public void invalidate(){invalidates++;}
}''',
'com/android/quickstep/T110SoftwareFrameTest.java':'''package com.android.quickstep;
import android.view.*;import android.os.Handler;
public class T110SoftwareFrameTest {
 static class Fixture {View v=new View();ViewRootImpl r=new ViewRootImpl();int calls;boolean canceled;
  Fixture(){v.root=r;r.view=v;}
  T110SoftwareFrameHandler handler(){return new T110SoftwareFrameHandler(v,()->calls++,()->canceled);}
  void frame(){v.observer.draw();Handler.drain();}
  void clean(){assert v.observer.listeners.isEmpty();assert r.callbacks.isEmpty();assert Handler.queue.isEmpty();}
 }
 public static void main(String[] a){
  Fixture f=new Fixture();assert f.handler().schedule();f.v.observer.draw();f.v.observer.draw();assert f.calls==0;Handler.drain();assert f.calls==0;assert f.v.invalidates==2;f.frame();assert f.calls==1;f.r.destroy();assert f.calls==1;f.clean();
  f=new Fixture();assert f.handler().schedule();f.canceled=true;f.frame();assert f.calls==0;f.clean();
  f=new Fixture();assert f.handler().schedule();f.v.observer.draw();f.r.destroy();assert f.calls==1;Handler.drain();assert f.calls==1;f.clean();
  f=new Fixture();f.v.observer.alive=false;assert !f.handler().schedule();f.clean();
  f=new Fixture();f.v.root=null;assert !f.handler().schedule();f.clean();
  f=new Fixture();assert f.handler().schedule();f.v.observer.draw();f.r.view=null;Handler.drain();assert f.calls==1;f.clean();
  f=new Fixture();assert f.handler().schedule();f.canceled=true;f.r.destroy();assert f.calls==0;f.clean();
  System.out.println("SOFTWARE_FRAME_LIFECYCLE_PASS: two draws, async completion, cancel, detach, dead observer, exactly once");
 }
}'''}
for name,text in files.items():
    dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text,encoding='utf-8')
src=Path('/root/t110-build/lineage20/packages/apps/Trebuchet/quickstep/src/com/android/quickstep/T110SoftwareFrameHandler.java')
(root/'com/android/quickstep/T110SoftwareFrameHandler.java').write_bytes(src.read_bytes())
jdk=Path('/root/t110-build/lineage20/prebuilts/jdk/jdk17/linux-x86/bin')
subprocess.run([str(jdk/'javac'),'-d',str(root/'classes')]+[str(f) for f in root.rglob('*.java')],check=True)
result=subprocess.check_output([str(jdk/'java'),'-ea','-cp',str(root/'classes'),'com.android.quickstep.T110SoftwareFrameTest'],text=True)
(root/'result.txt').write_text(result,encoding='utf-8');print(result)
