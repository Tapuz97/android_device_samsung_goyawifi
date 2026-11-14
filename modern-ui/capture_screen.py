"""One Android screenshot only; no continuous capture or logging."""
from pathlib import Path
import subprocess,sys
target=Path(sys.argv[1]);target.parent.mkdir(parents=True,exist_ok=True)
with target.open('wb') as output:
    subprocess.run([r'C:\Users\Gal\AppData\Local\Android\Sdk\platform-tools\adb.exe',
        '-s','3004523270272200','exec-out',
        'input keyevent 224 >/dev/null 2>&1; sleep 1; screencap -p 2>/dev/null'],stdout=output,check=True,timeout=45)
assert target.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
print(target)
