from pathlib import Path
import struct,hashlib,json,argparse,re
parser=argparse.ArgumentParser();parser.add_argument('--out-dir',default='out-uid-routing');parser.add_argument('--report',default='module-equivalence.json');parser.add_argument('--base-dir');parser.add_argument('--installed-wireless',action='store_true');args=parser.parse_args()
assert re.fullmatch(r'out-[a-z0-9-]+',args.out_dir)
assert args.base_dir is None or re.fullmatch(r'out-[a-z0-9-]+',args.base_dir)
assert re.fullmatch(r'[a-z0-9-]+\.json',args.report)
b=Path('/root/t110-build');p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
paths=['drivers/marvell/graphics/galcore_src/galcore.ko','drivers/marvell/sd8787/wlan_src/mlan.ko','drivers/marvell/sd8787/wlan_src/sd8xxx.ko','drivers/marvell/sd8787/mbtc_src/mbt8xxx.ko']
def sections(f):
 d=f.read_bytes();assert d[:6]==b'\x7fELF\x01\x01'
 hdr=struct.unpack_from('<16sHHIIIIIHHHHHH',d);off,size,count,strings=hdr[6],hdr[11],hdr[12],hdr[13]
 rows=[struct.unpack_from('<10I',d,off+i*size) for i in range(count)]
 h=rows[strings];names=d[h[4]:h[4]+h[5]];out={}
 for r in rows:
  name=names[r[0]:].split(b'\0',1)[0].decode()
  if r[2]&2 and name!='.note.gnu.build-id':
   data=bytes(r[5]) if r[1]==8 else d[r[4]:r[4]+r[5]]
   if name=='.modinfo':data=b'\0'.join(sorted(x for x in data.split(b'\0') if x and not x.startswith((b'srcversion=',b'intree='))))
   out[name]=hashlib.sha256(data).hexdigest()
 for r in rows:
  if r[1] not in (4,9) or not(rows[r[7]][2]&2):continue
  name=names[r[0]:].split(b'\0',1)[0].decode()
  syms=rows[r[6]];strsec=rows[syms[6]];strings=d[strsec[4]:strsec[4]+strsec[5]]
  def sym(index):
   sn,sv,ss,info,other,section=struct.unpack_from('<IIIBBH',d,syms[4]+index*syms[9])
   text=strings[sn:].split(b'\0',1)[0].decode()
   section_name=names[rows[section][0]:].split(b'\0',1)[0].decode() if section<len(rows) else str(section)
   return text,sv,ss,info,other,section_name
  entries=[]
  for at in range(r[4],r[4]+r[5],r[9]):
   offset,info=struct.unpack_from('<II',d,at)
   item=[offset,info&255,sym(info>>8)]
   if r[1]==4:item.append(struct.unpack_from('<i',d,at+8)[0])
   entries.append(item)
  out['RELOC:'+name]=hashlib.sha256(json.dumps(entries,sort_keys=True).encode()).hexdigest()
 return out
result={}
for name in paths:
 old=b/'out-display-i2c'/name;new=b/args.out_dir/name
 if Path(name).name in ('mlan.ko','sd8xxx.ko'):old=p/'evidence/stock-radio-reference/rebuilt'/Path(name).name
 if args.base_dir:old=b/args.base_dir/name
 if args.installed_wireless:
  filename=Path(name).name
  if filename in ('mlan.ko','sd8xxx.ko'):
   old=p/'work/device/samsung/t110_bringup/wifi/assets'/filename
   if not old.exists():old=p/'evidence/stock-radio-reference/rebuilt'/filename
  elif filename=='mbt8xxx.ko':old=p/'work/device/samsung/t110_bringup/bluetooth/assets'/filename
 if not old.exists():
  result[name]={'status':'NO_BASE_MODULE'};continue
 a,c=sections(old),sections(new);differences=[k for k in sorted(set(a)|set(c)) if a.get(k)!=c.get(k)]
 result[name]={'status':'ALLOC_AND_RELOCATIONS_IDENTICAL' if not differences else 'DIFFERENT','different_sections':differences,'old_sections':a,'new_sections':c,'old_file_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'new_file_sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'ignored_nonfunctional_metadata':['debug sections','GNU build-id','srcversion','intree']}
(p/'evidence/hardware-v35'/args.report).write_text(json.dumps(result,indent=2)+'\n')
for name,r in result.items():print(name,r['status'],r.get('different_sections'))
