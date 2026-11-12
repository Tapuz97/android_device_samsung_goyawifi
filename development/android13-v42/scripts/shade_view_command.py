"""Issue a diagnostic ViewServer command using this boot's captured window hashes."""
from pathlib import Path
import json,os,socket,subprocess,sys
p=Path(__file__).resolve().parents[1]
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(s):return subprocess.check_output(adb+['shell',s],timeout=30).decode()
def command(value):
    with socket.create_connection(('127.0.0.1',4939),timeout=30) as sock:
        sock.sendall((value+'\n').encode());chunks=[]
        while True:
            chunk=sock.recv(65536)
            if not chunk:break
            chunks.append(chunk);data=b''.join(chunks)
            if b'IEND\xaeB`\x82' in data or data.endswith(b'DONE\n') or data.endswith(b'DONE.\n'):break
        return b''.join(chunks)
try:
    if '00000000 00000000' in sh('service call window 3'):sh('service call window 1 i32 4939')
    subprocess.run(adb+['forward','tcp:4939','tcp:4939'],check=True,capture_output=True)
    if sys.argv[1]=='invalidate':print(command('INVALIDATE aea0783 com.android.systemui.shade.NotificationShadeWindowView@'+format(87600523,'x')).decode())
    elif sys.argv[1]=='capture':
        target=sys.argv[2];label=sys.argv[3];data=command('CAPTURE aea0783 '+target)
        assert data.startswith(b'\x89PNG'),data[:100]
        (p/'evidence/offline-v40'/(label+'.png')).write_bytes(data)
finally:
    sh('service call window 2')
    subprocess.run(adb+['forward','--remove','tcp:4939'],capture_output=True)
