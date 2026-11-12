from pathlib import Path
import struct,json,hashlib
root=Path(__file__).resolve().parents[1];dest=Path((root/'storage-diagnostics/CURRENT.txt').read_text().strip());stock=Path(r'\\wsl.localhost\Ubuntu\root\t110-build\stock-system.raw.img')
with stock.open('rb') as f:
 f.seek(1024+88);inode_size=struct.unpack('<H',f.read(2))[0];f.seek(112*4096+1024);expected=f.read(inode_size)
assert inode_size==256
assert (dest/'system-inode-block112.bin').read_bytes()[1024:1280]==expected
entries=[json.loads(x) for x in (dest/'system-read-scan-before.jsonl').read_text().splitlines() if x.strip()]
assert entries[-1]['complete'] and entries[-1]['bad_count']==4
bad=[x['bad_block'] for x in entries if 'bad_block' in x];assert bad==[250715,250728,250730,250731]
repair=dest/'proposed-dictionary-restoration';repair.mkdir(exist_ok=True)
manifest={'status':'PREPARED_NOT_WRITTEN','system_start_sector':1392640,'system_bytes':1594884096,'inode':1253,'inode_size':256,'inode_offset':112*4096+1024,'inode_matches_stock':True,'file':'/system/hdic/zh.hdb','file_bytes':6567404,'extent':{'logical_block_start':0,'physical_block_start':249237,'physical_block_end':250840},'blocks':[]}
(repair/'expected-inode.bin').write_bytes(expected)
def fnv(data):
 n=2166136261
 for c in data:n=((n^c)*16777619)&0xffffffff
 return n
with stock.open('rb') as f:
 for block in bad:
  assert 249237<=block<=250840
  f.seek(block*4096);data=f.read(4096);assert len(data)==4096
  (repair/f'block-{block}.bin').write_bytes(data)
  manifest['blocks'].append({'block':block,'absolute_sector':1392640+block*8,'file_offset':(block-249237)*4096,'bytes':4096,'sha256':hashlib.sha256(data).hexdigest(),'md5':hashlib.md5(data).hexdigest(),'fnv1a32':f'{fnv(data):08x}'})
manifest['inode_md5']=hashlib.md5(expected).hexdigest();manifest['inode_fnv1a32']=f'{fnv(expected):08x}'
(repair/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))