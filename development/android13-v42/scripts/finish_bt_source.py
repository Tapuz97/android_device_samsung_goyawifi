"""Reconcile the final init payload with the canonical device source for future builds."""
from pathlib import Path
import hashlib,json,shutil
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';f=p/'work/device/samsung/t110_bringup/bluetooth/init.t110.bluetooth.rc'
before=f.read_bytes();trigger=b'on property:init.svc.t110-radio-init=stopped\n    start t110-bluetooth-init\n\n';assert before.startswith(trigger)
after=before[len(trigger):];edit=json.loads((e/'v38-image-edit.json').read_text())
assert hashlib.sha256(after).hexdigest()==edit['updated_files']['system/vendor/etc/init/init.t110.bluetooth.rc']
record=e/'device-source-build-v37.json';assert not record.exists();shutil.copyfile(e/'device-source.json',record);f.write_bytes(after)
print('CANONICAL_VENDOR_INIT_MATCHES_CORRECTED_IMAGE')
