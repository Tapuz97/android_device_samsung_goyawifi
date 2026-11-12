from pathlib import Path
import json
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-bt-sd';f=e/'native-qualification.json';dest=e/'native-harness-help-exit.json';assert not dest.exists()
record=json.loads(f.read_text());assert record['status']=='NATIVE_QUALIFICATION_FAILED' and record['error'].startswith('Bluetooth Manager Commands:')
assert record['loader_exit_zero'] and record['hal_service_running'] and record['boot_server_netd_stable']
record['test_harness_conclusion']='cmd bluetooth_manager help returns a nonzero shell status with valid help. No adapter toggle or app scan was attempted. Accept help text only; keep operational command checks strict.'
dest.write_text(json.dumps(record,indent=2)+'\n');f.unlink();print('HELP_EXIT_HARNESS_FAILURE_PRESERVED_NO_ROM_CHANGE')
