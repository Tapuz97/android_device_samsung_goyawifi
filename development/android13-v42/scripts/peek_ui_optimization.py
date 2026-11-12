import os,re,subprocess
from pathlib import Path
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd):return subprocess.run(adb+['shell',cmd],capture_output=True,timeout=20).stdout.decode(errors='replace')
text=sh('ps -A');print('\n'.join(line for line in text.splitlines() if 'dex2oat' in line or 'system_server' in line))
print(sh('df -k /data'))
memory=sh('cat /proc/meminfo');print('\n'.join(line for line in memory.splitlines() if line.startswith(('MemFree:','SwapFree:','SwapTotal:'))))
