"""Inspect SystemUI DEX in the actual image and preserve keystore enforcement."""
from pathlib import Path
import hashlib,io,json,re,subprocess,tempfile,zipfile
b=Path('/root/t110-build');p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
e=p/'evidence/offline-v26'
def content(version,name):
 return subprocess.check_output(['debugfs','-R','cat '+name,str(b/f'export-lineage20-rom-v{version}/system.raw.img')],stderr=subprocess.DEVNULL)
apk=content(17,'/system/system_ext/priv-app/SystemUI/SystemUI.apk')
assert apk==(b/'out-system/target/product/t110_bringup/system/system_ext/priv-app/SystemUI/SystemUI.apk').read_bytes()
assert apk!=content(15,'/system/system_ext/priv-app/SystemUI/SystemUI.apk')
disassembler=b/'lineage20/prebuilts/sdk/tools/linux/bin/dexdump'
found=''
with tempfile.TemporaryDirectory(prefix='v26-dex-',dir=b) as temp:
 with zipfile.ZipFile(io.BytesIO(apk)) as z:
  for name in z.namelist():
   if not re.fullmatch(r'classes\d*\.dex',name):continue
   data=z.read(name)
   if b'AppOpsControllerImpl;' not in data:continue
   dex=Path(temp)/name;dex.write_bytes(data)
   proc=subprocess.Popen([str(disassembler),'-d',str(dex)],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,errors="replace")
   active=False; lines=[]
   for line in proc.stdout:
    if 'Class descriptor' in line:
     if active:break
     active="'Lcom/android/systemui/appops/AppOpsControllerImpl;'" in line
    if active:lines.append(line)
   if proc.poll() is None:proc.terminate()
   proc.wait()
   text=''.join(lines)
   if "name          : 'fetchCurrentActiveOps'" not in text:continue
   start=text.index("name          : 'fetchCurrentActiveOps'")
   method=text[start:]; nextmethod=re.search(r'\n    #\d+',method)
   if nextmethod:method=method[:nextmethod.start()]
   found=method;break
assert found,'Actual DEX method not found; inspect before changing verification'
(e/'SystemUI-fetchCurrentActiveOps-dex.txt').write_text(found)
# The API result must be tested before List.iterator. Null follows return-void.
call=found.index('getPackagesForOps:');iterator=found.index('List;.iterator:')
guard=found[call:iterator]
assert re.search(r'if-(?:eqz|nez)',guard) and 'return-void' in guard,guard
checks={}
for name in ['/system/bin/keystore2','/system/framework/framework.jar','/system/framework/services.jar']:
 new=content(17,name);old=content(15,name);assert new and new==old,name
 checks[name]=hashlib.sha256(new).hexdigest()
result=dict(status='PASS',SystemUI_apk_sha256=hashlib.sha256(apk).hexdigest(),
 actual_dex_null_guard=True,unchanged_security_components=checks,tablet_access=False,boots=0)
(e/'systemui-dex-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
