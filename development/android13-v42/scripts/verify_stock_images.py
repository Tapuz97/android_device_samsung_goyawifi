from pathlib import Path
import zipfile,tarfile,hashlib,re,json,struct,gzip
root=Path('firmware'); z=zipfile.ZipFile(next(root.glob('*.zip')))
name=next(n for n in z.namelist() if n.startswith('CODE_'))
p=root/name
if not p.exists():
 with z.open(name) as src,p.open('wb') as dst:
  import shutil
  shutil.copyfileobj(src,dst,4*1024*1024)
with p.open('rb') as f:
 f.seek(-256,2); tail=f.read()
m=re.search(rb'([0-9a-f]{32})[ \t]+[^\r\n]+\r?\n?$',tail)
assert m,repr(tail)
end=p.stat().st_size-256+m.start(); h=hashlib.md5()
with p.open('rb') as f:
 left=end
 while left:
  b=f.read(min(left,4*1024*1024));h.update(b);left-=len(b)
assert h.hexdigest()==m.group(1).decode(),(h.hexdigest(),m.group(1))
report={'ap_tar_md5':h.hexdigest(),'zip_entry_crc_checked':True,'images':{}}
with tarfile.open(p) as t:
 for name in ['boot.img','recovery.img']:
  b=t.extractfile(name).read(); out=root/'extracted'/name
  assert out.read_bytes()==b
  fields=struct.unpack_from('<10I',b,8)
  ks,ka,rs,ra,ss,sa,ta,pg,dt,unused=fields
  assert b[:8]==b'ANDROID!'; assert pg>=512
  d=root/'extracted'/name.replace('.img',''); d.mkdir(exist_ok=True)
  (d/'zImage').write_bytes(b[pg:pg+ks]); ro=pg+((ks+pg-1)//pg)*pg
  rb=b[ro:ro+rs];(d/'ramdisk.gz').write_bytes(rb)
  (d/'ramdisk.cpio').write_bytes(gzip.decompress(rb))
  report['images'][name]={'size':len(b),'sha256':hashlib.sha256(b).hexdigest(),'kernel_size':ks,'kernel_addr':hex(ka),'ramdisk_size':rs,'ramdisk_addr':hex(ra),'second_size':ss,'second_addr':hex(sa),'tags_addr':hex(ta),'page_size':pg,'dt_size':dt,'board':b[48:64].split(b'\0')[0].decode(),'cmdline':b[64:576].split(b'\0')[0].decode()}
(root/'verified-images.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
