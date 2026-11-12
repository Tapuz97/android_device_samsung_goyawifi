"""Prove omitted extracted firmware files are reproducible from the retained ZIP."""
from pathlib import Path
import zipfile,tarfile,hashlib,json
r=Path(__file__).resolve().parents[1];out=r/'backups/android13-before-lineage14-20261112'
manifest=json.loads((out/'project-restoration-members.json').read_text())
excluded={x['path']:x for x in manifest['excluded_redundant_files']}
code='firmware/CODE_T110XXUANI7_2751957_REV02_user_low_ship.tar.md5'
sparse='firmware/extracted/system.img.sparse'
def check(stream,item):
 h=hashlib.sha256();size=0
 for b in iter(lambda:stream.read(8*1024*1024),b''):h.update(b);size+=len(b)
 assert size==item['bytes'] and h.hexdigest()==item['sha256'],(size,h.hexdigest())
 return {'bytes':size,'sha256':h.hexdigest(),'verified':True}
with zipfile.ZipFile(r/'firmware/SM-T110_T110XXUANI7_T110OJVANI1.zip') as z:
 member=next(x for x in z.infolist() if Path(x.filename).name==Path(code).name)
 with z.open(member) as f:code_result=check(f,excluded[code])
with tarfile.open(r/code,'r:') as t:
 member=next(x for x in t if x.size==excluded[sparse]['bytes'] and 'system' in x.name)
 sparse_result=check(t.extractfile(member),excluded[sparse])
result={'status':'EXCLUDED_EXTRACTIONS_REPRODUCIBLE','zip_member':Path(code).name,'code_tar':code_result,'system_tar_member':member.name,'sparse_system':sparse_result}
(out/'firmware-derivation-verified.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
