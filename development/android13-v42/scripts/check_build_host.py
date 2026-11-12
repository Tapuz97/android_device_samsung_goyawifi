"""Bounded native Windows event/WSL reads; avoids the stalled PowerShell shell."""
from pathlib import Path
import subprocess,datetime
out=Path(__file__).resolve().parents[1]/'evidence/hardware-v35/host-storage-latest.txt'
query='*[System[(EventID=153 or EventID=129 or EventID=51) and TimeCreated[timediff(@SystemTime) <= 1800000]]]'
parts=[datetime.datetime.now().astimezone().isoformat()]
for args in (['wevtutil','qe','System','/q:'+query,'/rd:true','/c:5','/f:text'],['wsl.exe','--list','--verbose']):
    try:
        r=subprocess.run(args,capture_output=True,timeout=15)
        raw=r.stdout+r.stderr
        encoding='utf-16le' if b'\0' in raw[:80] else 'utf-8'
        parts.append(raw.decode(encoding,errors='replace'))
    except subprocess.TimeoutExpired:parts.append(args[0]+' timed out after15seconds')
text='\n'.join(parts);out.write_text(text,encoding='utf-8');print(text[-7000:])
