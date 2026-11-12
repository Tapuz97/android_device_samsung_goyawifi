package dev.tapuz.t110.interaction;

import android.system.Os;
import android.system.OsConstants;
import android.system.StructTimeval;
import java.io.FileDescriptor;
import java.net.SocketAddress;
import java.nio.*;
import java.nio.file.*;
import org.json.*;

/** Root-only bounded diagnostic: unmatched temporary rules, immediately deleted. */
public final class NetlinkRuleProbe {
    static byte[] attr(int type,byte[] value) {
        ByteBuffer b=ByteBuffer.allocate((value.length+7)&~3).order(ByteOrder.LITTLE_ENDIAN);
        b.putShort((short)(4+value.length)).putShort((short)type).put(value);return b.array();
    }
    static byte[] u32(int n){return ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN).putInt(n).array();}
    static byte[] packet(int action,int priority,boolean uid,boolean iif,boolean tableAttr) {
        java.io.ByteArrayOutputStream attributes=new java.io.ByteArrayOutputStream();
        try {
            attributes.write(attr(6,u32(priority)));
            if(tableAttr)attributes.write(attr(15,u32(31042)));
            attributes.write(attr(10,u32(0x5a5a5a5a)));attributes.write(attr(16,u32(-1)));
            if(uid)attributes.write(attr(20,ByteBuffer.allocate(8).order(ByteOrder.LITTLE_ENDIAN).putInt(0).putInt(0x7fffffff).array()));
            if(iif)attributes.write(attr(3,new byte[]{'l','o',0}));
        }catch(Exception impossible){throw new RuntimeException(impossible);}
        byte[] a=attributes.toByteArray();ByteBuffer b=ByteBuffer.allocate(28+a.length).order(ByteOrder.LITTLE_ENDIAN);
        b.putInt(b.capacity()).putShort((short)action).putShort((short)(action==32?0x605:5)).putInt(priority).putInt(0);
        b.put((byte)2).put((byte)0).put((byte)0).put((byte)0).put((byte)(tableAttr?0:250)).put((byte)0).put((byte)0).put((byte)1).putInt(0);
        b.put(a);return b.array();
    }
    static int request(FileDescriptor fd,byte[] bytes)throws Exception {
        Os.write(fd,bytes,0,bytes.length);byte[] response=new byte[2048];int n=Os.read(fd,response,0,response.length);
        if(n<20)throw new IllegalStateException("Short netlink reply");
        ByteBuffer b=ByteBuffer.wrap(response).order(ByteOrder.LITTLE_ENDIAN);
        if(b.getShort(4)!=2)throw new IllegalStateException("Expected netlink ACK/error");
        return b.getInt(16);
    }
    public static void main(String[] args)throws Exception {
        if(Os.getuid()!=0)throw new SecurityException("Root-only diagnostic");
        String cid=new String(Files.readAllBytes(Paths.get("/sys/block/mmcblk0/device/cid")),"UTF-8").trim();
        if(!"1101003030384745T110_ADB_SERIAL".equals(cid))throw new SecurityException("Wrong device");
        Class<?> addressType=Class.forName("android.system.NetlinkSocketAddress");
        SocketAddress kernel=(SocketAddress)addressType.getConstructor(int.class,int.class).newInstance(0,0);
        FileDescriptor fd=Os.socket(OsConstants.AF_NETLINK,OsConstants.SOCK_RAW,OsConstants.NETLINK_ROUTE);
        JSONArray out=new JSONArray();
        try {
            Os.class.getMethod("connect",FileDescriptor.class,SocketAddress.class).invoke(null,fd,kernel);
            Os.setsockoptTimeval(fd,OsConstants.SOL_SOCKET,OsConstants.SO_RCVTIMEO,StructTimeval.fromMillis(2000));
            boolean[][] cases={{true,true,true},{false,true,true},{true,false,true},{false,false,false}};
            for(int i=0;i<cases.length;i++) {
                boolean[] c=cases[i];int priority=31042+i;boolean added=false;
                JSONObject r=new JSONObject().put("priority",priority).put("uid_attribute",c[0]).put("loopback_attribute",c[1]).put("extended_table",c[2]);
                try {
                    int error=request(fd,packet(32,priority,c[0],c[1],c[2]));r.put("add_error",error);added=error==0;
                }finally {
                    if(added){int error=request(fd,packet(33,priority,c[0],c[1],c[2]));r.put("delete_error",error);if(error!=0)throw new IllegalStateException("Temporary rule cleanup failed: "+error);}
                }
                out.put(r);
            }
        }finally {Os.close(fd);}
        System.out.println(new JSONObject().put("temporary_mark","0x5a5a5a5a/full-mask").put("results",out).toString());
    }
}
