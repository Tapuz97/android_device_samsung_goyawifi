package dev.tapuz.t110.interaction;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.bluetooth.le.BluetoothLeScanner;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanResult;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Environment;
import android.os.storage.StorageManager;
import android.os.storage.StorageVolume;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

final class PeripheralAudit {
    static JSONObject bluetooth(Context context,boolean stateOnly) throws Exception {
        JSONObject result=new JSONObject();
        BluetoothManager manager=context.getSystemService(BluetoothManager.class);
        BluetoothAdapter adapter=manager==null?null:manager.getAdapter();
        result.put("adapter_present",adapter!=null);
        if(adapter==null)return result.put("completed",true);
        result.put("state",adapter.getState()).put("enabled",adapter.isEnabled());
        if(stateOnly)return result.put("completed",true);
        if(!adapter.isEnabled())return result.put("completed",true);
        result.put("originally_discovering",adapter.isDiscovering());
        AtomicInteger classicResults=new AtomicInteger();
        AtomicInteger classicStarts=new AtomicInteger();
        BroadcastReceiver receiver=new BroadcastReceiver(){
            @Override public void onReceive(Context c,Intent intent){
                if(BluetoothDevice.ACTION_FOUND.equals(intent.getAction()))classicResults.incrementAndGet();
                if(BluetoothAdapter.ACTION_DISCOVERY_STARTED.equals(intent.getAction()))classicStarts.incrementAndGet();
            }
        };
        IntentFilter filter=new IntentFilter();filter.addAction(BluetoothDevice.ACTION_FOUND);filter.addAction(BluetoothAdapter.ACTION_DISCOVERY_STARTED);
        boolean started=false;
        context.registerReceiver(receiver,filter,Context.RECEIVER_EXPORTED);
        try {
            if(!adapter.isDiscovering()) {
                started=adapter.startDiscovery();result.put("classic_start_return",started);
                Thread.sleep(6000);
                result.put("classic_discovering",adapter.isDiscovering()).put("classic_start_broadcasts",classicStarts.get());
            }
            result.put("classic_results",classicResults.get());
        } finally {
            if(started)result.put("classic_cancel_return",adapter.cancelDiscovery());
            context.unregisterReceiver(receiver);
        }
        Thread.sleep(1000);
        BluetoothLeScanner scanner=adapter.getBluetoothLeScanner();result.put("ble_scanner_present",scanner!=null);
        AtomicInteger bleResults=new AtomicInteger();AtomicInteger bleFailure=new AtomicInteger(-1);
        ScanCallback callback=new ScanCallback(){
            @Override public void onScanResult(int type,ScanResult r){bleResults.incrementAndGet();}
            @Override public void onBatchScanResults(List<ScanResult> results){bleResults.addAndGet(results.size());}
            @Override public void onScanFailed(int error){bleFailure.set(error);}
        };
        if(scanner!=null) {
            boolean scanStarted=false;
            try {scanner.startScan(callback);scanStarted=true;Thread.sleep(6000);}
            finally {if(scanStarted)scanner.stopScan(callback);}
        }
        return result.put("ble_results",bleResults.get()).put("ble_scan_failure",bleFailure.get())
            .put("state_after",adapter.getState()).put("peer_identifiers_collected",false).put("completed",true);
    }

    static JSONObject storage(Context context) throws Exception {
        StorageManager manager=context.getSystemService(StorageManager.class);JSONArray volumes=new JSONArray();
        for(StorageVolume volume:manager.getStorageVolumes())volumes.put(new JSONObject()
            .put("primary",volume.isPrimary()).put("removable",volume.isRemovable()).put("emulated",volume.isEmulated()).put("state",volume.getState()));
        JSONArray checks=new JSONArray();int passed=0;
        for(File dir:context.getExternalFilesDirs(null)) {
            if(dir==null)continue;
            boolean removable=Environment.isExternalStorageRemovable(dir);
            JSONObject item=new JSONObject().put("removable",removable).put("state",Environment.getExternalStorageState(dir));checks.put(item);
            if(!removable||!Environment.MEDIA_MOUNTED.equals(Environment.getExternalStorageState(dir)))continue;
            File file=null;
            try {
                byte[] original=new byte[65536];new java.util.Random(0x110137).nextBytes(original);
                file=File.createTempFile("t110-storage-",".bin",dir);
                if(!file.getCanonicalPath().startsWith(dir.getCanonicalPath()+File.separator))throw new SecurityException("Unexpected app storage path");
                try(FileOutputStream stream=new FileOutputStream(file)){stream.write(original);stream.getFD().sync();}
                byte[] actual=new byte[original.length];int used=0;
                try(FileInputStream stream=new FileInputStream(file)) {
                    while(used<actual.length){int n=stream.read(actual,used,actual.length-used);if(n<0)break;used+=n;}
                    if(stream.read()!=-1)throw new IllegalStateException("Unexpected extra file data");
                }
                boolean equal=used==actual.length&&Arrays.equals(original,actual);item.put("bytes",used).put("write_fsync_read_match",equal);
                if(equal)passed++;
            } catch(Exception error){item.put("error",error.toString());}
            finally {if(file!=null)item.put("test_file_removed",file.delete());}
        }
        return new JSONObject().put("volumes",volumes).put("external_app_directories",checks).put("removable_roundtrips_passed",passed).put("completed",true);
    }
}
