"""One bounded, metadata-only availability check of the disconnected/timed-out VHD."""
from pathlib import Path
import subprocess,json,sys,time
e=Path(__file__).resolve().parents[1]/'evidence/remote-fixes-20261110'
code="import os,json; s=os.stat(r'E:\\T110-build\\WSL\\ext4.vhdx'); print(json.dumps({'size':s.st_size,'mtime':s.st_mtime}))"
start=time.monotonic()
try:
    r=subprocess.run([sys.executable,'-c',code],capture_output=True,timeout=12)
    record={'status':'METADATA_ACCESSIBLE' if r.returncode==0 else 'UNAVAILABLE','returncode':r.returncode,'stdout':r.stdout.decode(errors='replace'),'stderr':r.stderr.decode(errors='replace')}
except subprocess.TimeoutExpired:record={'status':'METADATA_LOOKUP_TIMED_OUT','timeout_seconds':12}
record.update(elapsed_seconds=time.monotonic()-start,mode='READ_ONLY_SINGLE_STAT_NO_DISK_REPAIR')
(e/'external-build-access.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
