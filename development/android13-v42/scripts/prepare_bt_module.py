"""Restrict Marvell character nodes and support existing-firmware-only bring-up."""
from pathlib import Path
import difflib,hashlib,json,os,sys
assert os.environ.get('WSL_DISTRO_NAME')=='Ubuntu'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');src=Path('/root/t110-build/kernel-display-i2c')
e=p/'evidence/hardware-bt-sd';patch=p/'patches/0100-mbt8xxx-restrict-nodes-and-existing-firmware.patch'
record=e/'module-source.json'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
refresh='--refresh' in sys.argv
if record.exists():
 saved=json.loads(record.read_text())
 for row in saved['files']:assert sha(src/row['path'])==row['after_sha256'],row['path']
 if not refresh:print('BT_MODULE_SOURCE_ALREADY_APPLIED');raise SystemExit(0)
else:assert not patch.exists() and not refresh
prefix='drivers/marvell/sd8787/mbtc_src/bt/'
changes={}
for filename in ['bt_main.c','bt_sdiommc.c']:
 f=src/(prefix+filename);original=(p/'evidence/hardware-v35/bluetooth-source'/filename).read_text()
 before=original if refresh else f.read_text()
 assert before==original,filename
 after=before
 if filename=='bt_main.c':
  old='mbtchar_chmod(dev_file, 0666);';assert after.count(old)==4
  after=after.replace(old,'mbtchar_chmod(dev_file, 0660);')
 else:
  old='#include <linux/firmware.h>'
  assert after.count(old)==1
  after=after.replace(old,old+'''
#include <linux/module.h>

/* A shared Wi-Fi/BT chip may already run the matching combo firmware.
 * Bring-up can require that state without attempting a second download.
 */
static bool require_fw_ready;
module_param(require_fw_ready, bool, 0444);
MODULE_PARM_DESC(require_fw_ready,
                "Require active combo firmware; never download if it is absent");
''')
  old='\t/* Check if other interface is downloading */'
  assert after.count(old)==1
  after=after.replace(old,'''
\tif (require_fw_ready) {
\t\tPRINTM(ERROR, "BT: existing firmware required; download blocked\\n");
\t\tsdio_release_host(card->func);
\t\treturn BT_STATUS_FAILURE;
\t}
'''+old)
 changes[prefix+filename]=(before,after)
chunks=[];rows=[]
for name,(before,after) in changes.items():
 chunks.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),'a/'+name,'b/'+name))
 rows.append(dict(path=name,before_sha256=hashlib.sha256(before.encode()).hexdigest(),after_sha256=hashlib.sha256(after.encode()).hexdigest()))
patch.write_text(''.join(chunks))
for name,(_,after) in changes.items():(src/name).write_text(after)
record.write_text(json.dumps(dict(files=rows,patch_sha256=sha(patch),permissions='0660 system:bluetooth for BT; no world-writable nodes',probe_parameters='drv_mode=1 debug_intf=0 require_fw_ready=1'),indent=2)+'\n')
print('BT_MODULE_SOURCE_READY')
