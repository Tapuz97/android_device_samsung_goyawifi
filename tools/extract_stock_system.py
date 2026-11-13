"""Recover the matched stock SYSTEM from the preserved firmware ZIP, streaming CODE.tar."""
from pathlib import Path
import json
import shutil
import tarfile
import zipfile

ROOT=Path('/root/t110-lineage14/reference')
firmware=ROOT/'project-inputs/SM-T110/firmware/SM-T110_T110XXUANI7_T110OJVANI1.zip'
dest=ROOT/'stock-ani7'
dest.mkdir(exist_ok=True)
with zipfile.ZipFile(firmware) as package:
    names=package.namelist()
    print('Firmware ZIP members:', names, flush=True)
    code=next(n for n in names if 'CODE' in n.upper() and n.lower().endswith(('.tar','.tar.md5')))
    with package.open(code) as stream, tarfile.open(fileobj=stream,mode='r|') as tar:
        for member in tar:
            if member.isfile() and Path(member.name).name in ('system.img','system.img.ext4'):
                with tar.extractfile(member) as source,(dest/'system.sparse.img').open('wb') as output:
                    shutil.copyfileobj(source,output,length=1024*1024)
                print('Extracted stock sparse SYSTEM:',member.size,flush=True)
            if member.isfile() and Path(member.name).name in ('boot.img','recovery.img'):
                with tar.extractfile(member) as source,(dest/Path(member.name).name).open('wb') as output:
                    shutil.copyfileobj(source,output,length=1024*1024)
    # Finish ZIP verification through the entire uncompressed member (including MD5 trailer).
    with package.open(code) as stream:
        while stream.read(4*1024*1024): pass
(dest/'source.json').write_text(json.dumps({'firmware':str(firmware),'zip_member':code},indent=2)+'\n')
