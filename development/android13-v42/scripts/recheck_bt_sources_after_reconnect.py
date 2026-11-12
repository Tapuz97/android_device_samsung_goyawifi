from pathlib import Path
import hashlib,json,os
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/hardware-bt-sd';root=Path('/root/t110-build/lineage20')
g=json.loads((e/'lookup-watchdog-source.json').read_text());d=json.loads((e/'device-source.json').read_text())
files={root/'packages/modules/Bluetooth'/g['file']:g['after_sha256'],root/'device/samsung/t110_bringup/bluetooth/t110_bt_init.c':d['files']['bluetooth/t110_bt_init.c']}
for f,expected in files.items():assert hashlib.sha256(f.read_bytes()).hexdigest()==expected,str(f)
old=Path((e/'lookup-build-log.txt').read_text().strip()).read_bytes()
(e/'reconnect-build-check.json').write_text(json.dumps(dict(source_hashes_verified=True,old_log_null_bytes=old.count(b'\0'),old_log_contains_success=b'build completed successfully' in old,
 forced_recompile_sources=[str(f) for f in files]),indent=2)+'\n')
for f in files:os.utime(f,None)
print('SOURCE_HASHES_MATCH_FORCING_FRESH_COMPONENT_COMPILATION')
