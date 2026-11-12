from pathlib import Path
import hashlib,json,subprocess,sys
p=Path(sys.argv[1]);b=Path('/root/t110-build');src=b/'kernel-display-i2c'
r=json.loads((p/'evidence/offline-v34/display-i2c-source.json').read_text())
assert hashlib.sha256((b/'out-display-i2c/.config').read_bytes()).hexdigest()==r['config_sha256']
assert hashlib.sha256((src/'drivers/input/touchscreen/bt532_ts.c').read_bytes()).hexdigest()=='1a4706eafa67cdf68e5b08ca10c683d07e87910cae439d974715bbf9a0623484'
f=src/'drivers/gpu/ion/ion.c';before=f.read_bytes();patch=(p/'patches/0079-kernel-goya-ion-map-shared-buffer.patch').read_bytes()
assert hashlib.sha256(before).hexdigest() in ['ec43a5078a55a5ec4c078be235444c9db0d316a33b5ea6d9b126dab8a55a653c','0b6839e8a4d845a170e23e69c6b5c4489a948816f041d8c267f3a6911330eb8b']
if b'case ION_IOC_MAP:' not in before:
    subprocess.run(['patch','--dry-run','-p1'],cwd=src,input=patch,check=True)
    subprocess.run(['patch','-p1'],cwd=src,input=patch,check=True)
else:assert before.count(b'case ION_IOC_MAP:')==1
after=f.read_bytes()
original=after.replace(b'\tcase ION_IOC_SHARE:\n\tcase ION_IOC_MAP:',b'\tcase ION_IOC_SHARE:')
assert original==before or before==after
assert hashlib.sha256(original).hexdigest()=='ec43a5078a55a5ec4c078be235444c9db0d316a33b5ea6d9b126dab8a55a653c'
assert hashlib.sha256(after).hexdigest()=='0b6839e8a4d845a170e23e69c6b5c4489a948816f041d8c267f3a6911330eb8b'
(p/'evidence/remote-fixes-20261110/ion-kernel-source.json').write_text(json.dumps({'source':str(f),'before_sha256':hashlib.sha256(original).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),'only_change':'ION_IOC_MAP aliases ION_IOC_SHARE as in android-common-3.4','config_sha256':r['config_sha256'],'touch_retained':True},indent=2)+'\n')
