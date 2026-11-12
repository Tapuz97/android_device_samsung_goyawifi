from pathlib import Path
import os, socket, subprocess, json
p=Path(__file__).resolve().parents[1]
e=p/'hardware-tests/20261107-200616-core'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd): return subprocess.check_output(adb+['shell',cmd],timeout=25).decode()
assert sh('getprop ro.secure').strip()=='0'
assert '00000000 00000000' in sh('service call window 3')
sh('input keyevent WAKEUP; wm dismiss-keyguard; cmd statusbar expand-notifications; sleep 2')
def command(value):
    with socket.create_connection(('127.0.0.1',4939),timeout=20) as sock:
        sock.sendall((value+'\n').encode()); chunks=[]
        while True:
            try:
                chunk=sock.recv(65536)
            except TimeoutError:
                print('VIEW_CAPTURE_TIMEOUT_BYTES',sum(map(len,chunks)),flush=True)
                break
            if not chunk: break
            chunks.append(chunk)
            joined=b''.join(chunks)
            if b'IEND\xaeB`\x82' in joined or joined.endswith(b'DONE\n'): break
        return b''.join(chunks)
try:
    started=sh('service call window 1 i32 4939')
    assert '00000001' in started, started
    subprocess.run(adb+['forward','tcp:4939','tcp:4939'],check=True,capture_output=True)
    for name, target in [('trust-row', 'com.android.systemui.statusbar.notification.row.ExpandableNotificationRow@'+format(217846773,'x')),
                         ('notification-root','com.android.systemui.shade.NotificationShadeWindowView@3b3b3c3'),
                         ('notification-stack','com.android.systemui.statusbar.notification.stack.NotificationStackScrollLayout@3c129ed'),
                         ('notification-qs','com.android.systemui.qs.QSContainerImpl@f6f6183')]:
        data=command('CAPTURE 8768aa9 '+target)
        assert data.startswith(b'\x89PNG'), data[:80]
        (e/(name+'-view.png')).write_bytes(data)
        print(name,len(data),flush=True)
    print(command('INVALIDATE 8768aa9 com.android.systemui.shade.NotificationShadeWindowView@3b3b3c3').decode(errors='replace'))
finally:
    sh('service call window 2')
    subprocess.run(adb+['forward','--remove','tcp:4939'],capture_output=True)
