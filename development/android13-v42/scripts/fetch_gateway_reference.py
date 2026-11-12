from pathlib import Path
import base64,hashlib,json,urllib.request
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35/uid-upstream'
revision='cf10b7e6209c43acf70f82b8d01997ffece88835'
url='https://android.googlesource.com/kernel/msm/+/'+revision+'/net/ipv4/fib_semantics.c?format=TEXT'
data=base64.b64decode(urllib.request.urlopen(url,timeout=45).read(),validate=True)
target=e/'hammerhead-net_ipv4_fib_semantics.c'
if target.exists():assert target.read_bytes()==data
else:target.write_bytes(data)
(e/'gateway-reference.json').write_text(json.dumps(dict(url=url,revision=revision,sha256=hashlib.sha256(data).hexdigest()),indent=2)+'\n',encoding='utf-8')
print('PINNED_ANDROID_REFERENCE',len(data))
url='https://raw.githubusercontent.com/torvalds/linux/v4.3/net/ipv4/fib_semantics.c'
data=urllib.request.urlopen(url,timeout=45).read()
target=e/'mainline-v4.3-net_ipv4_fib_semantics.c'
if target.exists():assert target.read_bytes()==data
else:target.write_bytes(data)
(e/'gateway-mainline-reference.json').write_text(json.dumps(dict(url=url,tag='v4.3',sha256=hashlib.sha256(data).hexdigest()),indent=2)+'\n',encoding='utf-8')
print('MAINLINE_REFERENCE',len(data))
