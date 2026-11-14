from pathlib import Path
import subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from recovery_transport import ADB,SERIAL,BASE
dest=BASE/'tests/android13-complete-20261114/touch-events.txt'
with dest.open('wb') as out:
    p=subprocess.Popen([ADB,'-s',SERIAL,'shell','getevent','-lt','/dev/input/event1'],
        stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.PIPE)
    try:p.wait(timeout=90)
    except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
print('Finished bounded physical touchscreen capture:',dest)
