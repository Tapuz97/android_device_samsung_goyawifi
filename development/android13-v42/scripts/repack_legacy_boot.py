"""Repack legacy Android boot image with a replacement kernel, preserving geometry.
Produces a diagnostic image only. Does not flash. Rejects DT/second-stage images.
"""
import argparse,struct,hashlib,json,tarfile
from pathlib import Path

def repack(template,kernel):
 old=template.read_bytes(); assert old[:8]==b'ANDROID!'
 ks,ka,rs,ra,ss,sa,ta,page,dt,_=struct.unpack_from('<10I',old,8)
 assert page==2048 and ss==0 and dt==0
 align=lambda n:(n+page-1)//page*page
 rd=old[page+align(ks):page+align(ks)+rs]
 oldk=old[page:page+ks]
 def image_id(k):
  h=hashlib.sha1()
  for data in (k,rd,b''):h.update(data);h.update(struct.pack('<I',len(data)))
  return h.digest()+b'\0'*12
 assert old[576:608]==image_id(oldk),'Unsupported legacy image ID'
 k=kernel.read_bytes();header=bytearray(old[:page]);struct.pack_into('<I',header,8,len(k));header[576:608]=image_id(k)
 tail=old[page+align(ks)+align(rs):]
 out=bytes(header)+k+b'\0'*(align(len(k))-len(k))+rd+b'\0'*(align(rs)-rs)+tail
 assert len(out)<=16777216
 return out

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--template',type=Path,required=True);p.add_argument('--kernel',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 b=repack(a.template,a.kernel);a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('xb') as f:f.write(b)
 print(json.dumps({'path':str(a.output),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'status':'UNTESTED diagnostic kernel replacement; not modern Android'},indent=2))
if __name__=='__main__':main()
