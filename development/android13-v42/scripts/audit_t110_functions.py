"""Collect bounded evidence for the functional audit; never repairs or flashes."""
from pathlib import Path
import concurrent.futures,json,os,subprocess,time
p=Path(__file__).resolve().parents[1];e=p/'evidence/functional-audit-20261110';e.mkdir(parents=True,exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
cid=subprocess.check_output(adb+['shell','cat /sys/block/mmcblk0/device/cid'],timeout=10).decode().strip()
assert cid=='1101003030384745T110_ADB_SERIAL'
commands={
'identity': 'getprop ro.product.model; getprop ro.build.version.release; getprop ro.build.version.sdk; cat /proc/sys/kernel/random/boot_id; pidof system_server; pidof com.android.systemui; getprop sys.boot_completed; getprop sys.user.0.ce_available; getprop ro.crypto.state; getprop ro.crypto.type; getenforce; date +%s; getprop persist.sys.timezone; cat /proc/uptime',
'features': 'pm list features; pm list packages -s; cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.HOME',
'services': 'service list; ps -A',
'hal-services':'lshal',
'wifi':'cmd wifi status; dumpsys wifi',
'bluetooth':'dumpsys bluetooth_manager',
'camera':'dumpsys media.camera; cmd package resolve-activity --brief -a android.media.action.STILL_IMAGE_CAMERA',
'audio':'dumpsys audio; dumpsys media.audio_flinger; dumpsys media.audio_policy; cat /proc/asound/cards; cat /proc/asound/pcm',
'sensors':'dumpsys sensorservice; ls /sys/class/sensors; cat /proc/bus/input/devices',
'display':'wm size; wm density; dumpsys display; cat /sys/class/graphics/fb0/virtual_size /sys/class/graphics/fb0/stride /sys/class/graphics/fb0/bits_per_pixel; ls /sys/class/backlight',
'input':'dumpsys input; ime list -s; settings get secure default_input_method; settings get --lineage system force_show_navbar',
'battery':'dumpsys battery; for p in /sys/class/power_supply/*/uevent; do echo $p; cat $p; done',
'power':'dumpsys power; cat /sys/power/state; cat /sys/power/wakeup_count; cat /proc/wakelocks',
'usb':'dumpsys usb; getprop sys.usb.config; getprop sys.usb.state; ls /sys/class/android_usb/android0; ls /sys/class/android_usb/android0/f_*',
'storage':'sm list-disks; sm list-volumes all; df -k /data /storage/emulated/0; dumpsys mount; cat /proc/partitions',
'location':'dumpsys location',
'connectivity':'dumpsys connectivity; ip addr; ip route; settings get global airplane_mode_on',
'ime':'dumpsys input_method',
'webview':'dumpsys webviewupdate',
'user-security':'dumpsys user; dumpsys trust; locksettings get-disabled; getprop ro.adb.secure; getprop ro.secure; getprop ro.debuggable',
'notifications':'dumpsys notification --noredact',
'alarm-time':'dumpsys alarm; getprop persist.sys.timezone; for p in /sys/class/rtc/rtc0/date /sys/class/rtc/rtc0/time; do cat $p; done',
'accessibility':'dumpsys accessibility; settings get secure enabled_accessibility_services',
'packages-state':'dumpsys package com.android.settings; dumpsys package org.lineageos.lineageparts; dumpsys package org.lineageos.updater; dumpsys package com.android.inputmethod.latin',
'runtime-errors':'logcat -b crash -d -v threadtime; logcat -b events -d | grep -E "am_anr|am_crash|am_kill|wm_boot_animation_done" | tail -40',
'native-wallpaper':'dumpsys wallpaper; pm path org.lineageos.t110.wallpapers',
'kernel-capabilities':'zcat /proc/config.gz | grep -E "CONFIG_(BT|WLAN|MWIFIEX|LIBERTAS|VIBRATOR|SND|VIDEO|USB_MTP|USB_OTG|INPUT|EXT4|CMA|DMA_CMA|HIGH_RES_TIMERS|RTC)"; cat /proc/modules; cat /proc/dma-mappings',
'permissions-vintf':'ls /system/vendor/etc/permissions; cat /system/vendor/etc/vintf/manifest.xml; ls /system/lib/hw; ls /system/vendor/lib/hw; ls /system/vendor/bin/hw',
}
def collect(item):
    name,command=item;start=time.monotonic()
    try:
        r=subprocess.run(adb+['shell',command],capture_output=True,timeout=35)
        (e/(name+'.txt')).write_bytes(r.stdout+b'\nSTDERR:\n'+r.stderr)
        return name,{'exit_code':r.returncode,'seconds':round(time.monotonic()-start,2),'bytes':len(r.stdout),'command':command}
    except subprocess.TimeoutExpired as x:
        (e/(name+'.txt')).write_bytes((x.stdout or b'')+b'\nAUDIT_COMMAND_TIMEOUT\n'+(x.stderr or b''))
        return name,{'timeout':True,'seconds':round(time.monotonic()-start,2),'command':command}
record={'collected_at_host_epoch':time.time(),'mode':'READ_ONLY_NO_FIXES','commands':{}}
# Two service reads at most; avoid flooding the legacy tablet with parallel dumps.
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    for name,result in pool.map(collect,commands.items()):
        record['commands'][name]=result
        (e/'collection.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
        print(name,result.get('exit_code','TIMEOUT'),result.get('bytes',0),flush=True)
print('FUNCTIONAL_EVIDENCE_COLLECTED_NO_FIXES',flush=True)
