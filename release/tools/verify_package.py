"""Read-only verification. Does not call ADB, flash, mount or alter any image."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

def digest(stream):
    h=hashlib.sha256();size=0
    for block in iter(lambda:stream.read(1024*1024),b''):
        h.update(block);size+=len(block)
    return h.hexdigest(),size

def verify(root):
    root=Path(root).resolve()
    m=json.loads((root/'manifest.json').read_text())
    if m['device']!='SM-T110' or m['android']!='7.1.2':
        raise ValueError('Unexpected package target')
    names=set()
    for f in m['files']:
        p=(root/f['path']).resolve();p.relative_to(root)
        if f['path'] in names:raise ValueError('Duplicate payload')
        names.add(f['path'])
        with p.open('rb') as s: actual=digest(s)
        if actual!=(f['sha256'],f['bytes']):raise ValueError('Payload mismatch: '+f['path'])
        print('PASS',f['path'])
    if names!={'payload/boot.img','payload/system.raw.img.gz'}:
        raise ValueError('Missing or unexpected payload')
    with gzip.open(root/'payload/system.raw.img.gz','rb') as s: actual=digest(s)
    if actual!=(m['raw_system_sha256'],m['raw_system_bytes']):
        raise ValueError('Decompressed system mismatch')
    with (root/'payload/boot.img').open('rb') as s:
        if s.read(8)!=b'ANDROID!':raise ValueError('Invalid boot header')
    print('PASS complete decompressed system and boot header')
    print('Integrity passed; hardware compatibility and installation are separate checks.')

if __name__=='__main__':
    try:verify(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
    except (ValueError,KeyError,OSError,EOFError) as e:
        print('FAIL:',e,file=sys.stderr);sys.exit(1)
