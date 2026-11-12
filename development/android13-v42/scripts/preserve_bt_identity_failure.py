from pathlib import Path
import json
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';f=e/'native-qualification.json';dest=e/'native-before-identity-mode-fix.json';assert not dest.exists()
record=json.loads(f.read_text());assert record['status']=='NATIVE_QUALIFICATION_FAILED' and record['boot_server_netd_stable']
assert (e/'identity-mode-live-fix.json').exists();record['conclusion']='Init umask created controller_address0600 instead of0640. HAL open silently failed; file mode corrected without changing its identity. Permanent loader fchmod change is being built.'
dest.write_text(json.dumps(record,indent=2)+'\n');f.unlink();print('IDENTITY_MODE_FAILURE_PRESERVED')
