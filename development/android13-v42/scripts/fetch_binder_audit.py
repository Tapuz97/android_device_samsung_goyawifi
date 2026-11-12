from pathlib import Path
import urllib.request,json,hashlib,datetime
root=Path(__file__).resolve().parents[1];rev='915ad642e331e0f8ea107b5f5519f2c6f1e7e01c'
files={'cmds/servicemanager/Access.cpp':'los20-sm-Access.cpp','cmds/servicemanager/main.cpp':'los20-sm-main.cpp','libs/binder/ProcessState.cpp':'los20-ProcessState.cpp','libs/binder/IPCThreadState.cpp':'los20-IPCThreadState.cpp','libs/binder/Android.bp':'los20-binder-Android.bp'}
records=[]
for source,name in files.items():
 url=f'https://raw.githubusercontent.com/LineageOS/android_frameworks_native/{rev}/{source}'
 content=urllib.request.urlopen(url,timeout=25).read();(root/'evidence'/name).write_bytes(content)
 records.append({'url':url,'file':name,'sha256':hashlib.sha256(content).hexdigest()})
(root/'evidence/los20-binder-source-lock.json').write_text(json.dumps({'revision':rev,'fetched_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':records},indent=2)+'\n')
print('Saved 5 pinned Binder audit files')