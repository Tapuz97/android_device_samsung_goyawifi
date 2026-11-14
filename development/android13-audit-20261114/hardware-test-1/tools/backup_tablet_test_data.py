"""Private pre-flash data archive; old TWRP lacks binary-safe exec-out."""
from pathlib import Path
import gzip,hashlib,json,socket,subprocess,sys,tarfile,time
TOOLS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(TOOLS))
from recovery_transport import adb, shell
DEST=Path(r'\\wsl.localhost\Ubuntu\root\t110-android13-audit\hardware-test-20261114')
DEST.mkdir(exist_ok=True)
assert adb('get-state').strip()=='recovery'
assert adb('shell','cat /sys/block/mmcblk0/device/cid').strip()=='11010030303847453004523270272200'
assert 'loop0' not in adb('shell','cat /proc/mounts')
stream=DEST/'backup-stream.sh'
stream.write_bytes(b'#!/sbin/sh\n/sbin/busybox tar -cf - -C /data/local/tmp t110-rom-data t110-rom-data.pre-gapps t110-bootlogs 2>/tmp/t110-private-backup.stderr\nresult=$?\necho "$result" > /tmp/t110-private-backup.exit\nexit "$result"\n')
adb('push',stream,'/tmp/t110-private-backup-stream.sh')
shell('chmod 0700 /tmp/t110-private-backup-stream.sh')
server=subprocess.Popen([r'C:\Users\Gal\AppData\Local\Android\Sdk\platform-tools\adb.exe','-s','3004523270272200',
    'shell','/sbin/busybox','nc','-l','-p','32919','-e','/tmp/t110-private-backup-stream.sh'],
    stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
out=DEST/'old-android13-data-private.tar.gz'
forwarded=False
try:
    for attempt in range(30):
        rows=adb('shell','cat /proc/net/tcp /proc/net/tcp6').splitlines()
        if any(len(row.split())>3 and row.split()[1].endswith(f':{32919:04X}') and row.split()[3]=='0A' for row in rows):break
        if server.poll() is not None:raise RuntimeError(server.stderr.read().decode(errors='replace'))
        time.sleep(0.5)
    else:raise RuntimeError('Private tablet socket did not start listening')
    adb('forward','tcp:32919','tcp:32919')
    forwarded=True
    for attempt in range(30):
        try:
            connection=socket.create_connection(('127.0.0.1',32919),timeout=10);break
        except OSError:
            if server.poll() is not None:raise RuntimeError(server.stderr.read().decode(errors='replace'))
            time.sleep(1)
    else:raise RuntimeError('Private stream did not become available')
    connection.settimeout(120)
    total=0;last=time.monotonic()
    with connection, out.open('wb') as file, gzip.GzipFile(filename='',mode='wb',compresslevel=3,fileobj=file,mtime=0) as zipped:
        while data:=connection.recv(1024*1024):
            zipped.write(data);total+=len(data)
            if time.monotonic()-last>30:
                print(f'Archived {total//(1024*1024)} MiB of old test data.',flush=True);last=time.monotonic()
    server.wait(timeout=30)
    assert adb('shell','cat /tmp/t110-private-backup.exit').strip()=='0',adb('shell','cat /tmp/t110-private-backup.stderr')
    # Full decompression checks gzip CRC/truncation; tar iteration checks headers.
    decompressed=0
    with gzip.open(out,'rb') as f:
        while block:=f.read(1024*1024):decompressed+=len(block)
    assert decompressed==total
    with tarfile.open(out,'r:gz') as archive:
        members=list(archive)
    roots={m.name.split('/')[0] for m in members}
    assert roots=={'t110-rom-data','t110-rom-data.pre-gapps','t110-bootlogs'},roots
    digest=hashlib.sha256()
    with out.open('rb') as f:
        while block:=f.read(1024*1024):digest.update(block)
    result=dict(status='PASS_PRIVATE_LOCAL_ARCHIVE_READBACK',archive=str(out),sha256=digest.hexdigest(),
        compressed_bytes=out.stat().st_size,tar_bytes=total,members=len(members),roots=sorted(roots),
        tablet_mode='recovery',personal_data_uploaded=False,working14_data_modified=False)
    (DEST/'private-data-backup-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
finally:
    if server.poll() is None:server.terminate()
    if forwarded:adb('forward','--remove','tcp:32919')
