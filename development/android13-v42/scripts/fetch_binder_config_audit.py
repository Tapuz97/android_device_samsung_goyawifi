from pathlib import Path
import urllib.request,json,hashlib,base64
root=Path(__file__).resolve().parents[1]
urls={
 'los20-soong_config.mk':'https://raw.githubusercontent.com/LineageOS/android_build/f3bb11d8739b84a311a40a3069dc4cfca688be22/core/soong_config.mk',
 'aosp13-hwbinder-IPCThreadState.cpp':'https://android.googlesource.com/platform/system/libhwbinder/+/refs/tags/android-13.0.0_r1/IPCThreadState.cpp?format=TEXT',
 'aosp13-hwbinder-ProcessState.cpp':'https://android.googlesource.com/platform/system/libhwbinder/+/refs/tags/android-13.0.0_r1/ProcessState.cpp?format=TEXT'}
records=[]
for name,url in urls.items():
 data=urllib.request.urlopen(url,timeout=25).read()
 if 'format=TEXT' in url:data=base64.b64decode(data)
 (root/'evidence'/name).write_bytes(data)
 records.append({'file':name,'url':url,'sha256':hashlib.sha256(data).hexdigest()})
(root/'evidence/los20-extra-binder-sources.json').write_text(json.dumps(records,indent=2)+'\n')