from pathlib import Path
import hashlib,json,shutil,subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/hardware-v35/netd-event';b=Path('/root/t110-build')
log=Path((e/'build-log.txt').read_text().strip());assert 'build completed successfully' in log.read_text(errors='replace')
product=b/'out-system/target/product/t110_bringup'
matches=list((product/'data').rglob('netd_idletimer_event_test'));matches=[f for f in matches if f.is_file()]
assert len(matches)==1,matches
target=e/'netd_idletimer_event_test';shutil.copyfile(matches[0],target)
record=dict(source=str(matches[0]),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),netd_sha256=hashlib.sha256((product/'system/bin/netd').read_bytes()).hexdigest())
(e/'compiled.json').write_text(json.dumps(record,indent=2)+'\n');print('NETD_AND_TEST_COMPILED',record['netd_sha256'])
