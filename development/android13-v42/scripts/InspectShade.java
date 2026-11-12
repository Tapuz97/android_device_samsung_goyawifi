import com.sun.jdi.*;
import com.sun.jdi.connect.*;
import java.util.*;

/** Read private drawing state without suspending or invoking methods in SystemUI. */
class InspectShade {
  static Field field(ObjectReference o, String n) {
    for (Field f : o.referenceType().allFields()) if(f.name().equals(n)) return f;
    return null;
  }
  static Value get(ObjectReference o, String n) {
    Field f=field(o,n); return f==null?null:o.getValue(f);
  }
  static String describe(Value v) {
    if(v instanceof ArrayReference a) return a.getValues().toString();
    if(v instanceof ObjectReference o && o.referenceType().name().equals("android.graphics.Rect")) {
      return "Rect("+get(o,"left")+","+get(o,"top")+","+get(o,"right")+","+get(o,"bottom")+")";
    }
    return String.valueOf(v);
  }
  public static void main(String[] args) throws Exception {
    var c=Bootstrap.virtualMachineManager().attachingConnectors().stream()
      .filter(x->x.name().equals("com.sun.jdi.SocketAttach")).findFirst().orElseThrow();
    var a=c.defaultArguments();a.get("hostname").setValue("127.0.0.1");a.get("port").setValue("8701");
    VirtualMachine vm=c.attach(a);
    try {
      for(String cls : new String[]{"com.android.systemui.statusbar.notification.stack.NotificationStackScrollLayout", "com.android.systemui.statusbar.notification.row.ExpandableNotificationRow", "com.android.systemui.qs.QSContainerImpl"}) {
        for(ReferenceType t : vm.classesByName(cls)) for(ObjectReference o:t.instances(20)) {
          if(args.length==2 && args[0].equals("roundClip") && cls.endsWith("NotificationStackScrollLayout")) {
            boolean enabled=Boolean.parseBoolean(args[1]);
            Field f=field(o,"mShouldUseRoundedRectClipping");
            System.out.println("PROBE rounded clipping "+o.getValue(f)+" -> "+enabled);
            o.setValue(f,vm.mirrorOf(enabled));
          }
          System.out.println("OBJECT "+o);
          for(String n : new String[]{"mEntry","mRoundedRectClippingLeft","mRoundedRectClippingTop","mRoundedRectClippingRight","mRoundedRectClippingBottom","mBgCornerRadii","mShouldUseRoundedRectClipping","mLaunchingNotification","mRequestedClipBounds","mClipBounds","mPrivateFlags","mPrivateFlags2","mPrivateFlags3","mGroupFlags","mLayerType","mCachingFailed","mActualHeight","mClipTopAmount","mClipBottomAmount","mOwnTranslationZ","mBackgroundNormal","mNotificationParent","mHeadsUp","mIsHeadsUp","mIsPinned","mExpandAnimationRunning","mOutlineRect","mCustomOutline","mClipToActualHeight","mTopRoundness","mBottomRoundness","mDrawingRect"}) {
            Field f=field(o,n); if(f!=null) System.out.println("  "+n+"="+describe(o.getValue(f)));
          }
          Value entry=get(o,"mEntry");if(entry instanceof ObjectReference e) System.out.println("  KEY="+get(e,"mKey"));
          if(args.length==2 && args[0].equals("finiteRow") && cls.endsWith("ExpandableNotificationRow")) {
            ObjectReference r=(ObjectReference)get(o,"mClipBounds");
            boolean finite=Boolean.parseBoolean(args[1]);
            r.setValue(field(r,"left"),vm.mirrorOf(finite?-600:Integer.MIN_VALUE));
            r.setValue(field(r,"right"),vm.mirrorOf(finite?1200:Integer.MAX_VALUE));
            System.out.println("PROBE row bounds="+describe(r));
          }
        }
      }
    } finally {vm.dispose();}
  }
}
