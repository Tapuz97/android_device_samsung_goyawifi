"""Canonical noninteractive transport for this installed old TWRP; never feed scripts over a PTY."""
from pathlib import Path
import subprocess,hashlib
BASE=Path(__file__).resolve().parents[1]
ADB=r'C:\Users\Gal\AppData\Local\Android\Sdk\platform-tools\adb.exe'
SERIAL='3004523270272200'
def adb(*args,timeout=300):
 p=subprocess.run([ADB,'-s',SERIAL,*map(str,args)],stdin=subprocess.DEVNULL,capture_output=True,timeout=timeout)
 out=p.stdout.decode(errors='replace').replace('\r','')
 if p.returncode:raise RuntimeError('ADB command failed: '+str(args[:2])+' '+p.stderr.decode(errors='replace')[-400:])
 return out

def shell(commands,timeout=300):
 step=BASE/'install-step.sh'
 step.write_bytes(('set -e\n'+commands+'\nprintf "\\n__T110_SCRIPT_COMPLETED__\\n"\nexit\n').encode())
 adb('push',step,'/tmp/t110-verified-step.sh')
 out=adb('shell','/sbin/sh','/tmp/t110-verified-step.sh',timeout=timeout)
 if '__T110_SCRIPT_COMPLETED__' not in [x.strip() for x in out.splitlines()]:raise RuntimeError('Recovery script failed: '+out[-800:])
 return out

def remote_hash(p,timeout=600):return adb('shell','sha256sum',p,timeout=timeout).split()[0]
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while chunk:=f.read(1024*1024):h.update(chunk)
 return h.hexdigest()
