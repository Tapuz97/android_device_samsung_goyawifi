"""Compare Search's boot-classpath header with already compiled installed UI code."""
from pathlib import Path
import json,os,subprocess,zipfile
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112'
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
def sh(cmd):
    r=subprocess.run(adb+['shell',cmd],capture_output=True,timeout=30);assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace');return r.stdout.decode().replace('\r','').strip()
paths=sh('ls /data/dalvik-cache/arm/*SystemUI*classes.dex /system/system_ext/priv-app/SystemUI/oat/arm/SystemUI.odex').splitlines()
def header(data):
    result={}
    for key in ['bootclasspath','bootclasspath-checksums','classpath','compiler-filter','compilation-reason']:
        marker=b'\0'+key.encode()+b'\0';index=data.find(marker);assert index>=0,key
        result[key]=data[index+len(marker):].split(b'\0',1)[0].decode()
    return result
with zipfile.ZipFile(e/'private-search-preopt/Velvet-preopt.zip') as archive:
    with archive.open('system/product/priv-app/Velvet/oat/arm/Velvet.odex') as stream:search=header(stream.read(65536))
record=dict(search=search,comparisons={})
for name in paths:
    assert name.startswith(('/data/dalvik-cache/arm/','/system/system_ext/'))
    r=subprocess.run(adb+['exec-out',f'dd if={name} bs=4096 count=16'],capture_output=True,timeout=30);assert r.returncode==0
    other=header(r.stdout);record['comparisons'][name]=dict(header=other,bootclasspath_matches=other['bootclasspath']==search['bootclasspath'],bootclasspath_checksums_match=other['bootclasspath-checksums']==search['bootclasspath-checksums'])
(e/'runtime-art-header-comparison.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({name:{key:value for key,value in item.items() if key!='header'} for name,item in record['comparisons'].items()},indent=2))
