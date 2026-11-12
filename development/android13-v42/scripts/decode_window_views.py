"""Decode Android's documented ViewHierarchyEncoder binary window dump."""
from pathlib import Path
import io, json, struct, sys, zipfile

def decode(data):
    if not data:
        return []
    stream = io.BytesIO(data)
    def read():
        tag = stream.read(1)
        formats = {b'Z': '?', b'B': 'b', b'S': 'h', b'I': 'i', b'J': 'q', b'F': 'f', b'D': 'd'}
        if tag in formats:
            fmt = '>' + formats[tag]
            return struct.unpack(fmt, stream.read(struct.calcsize(fmt)))[0]
        if tag == b'R':
            size = struct.unpack('>h', stream.read(2))[0]
            return stream.read(size).decode('utf-8', errors='replace')
        if tag == b'M':
            result = {}
            while True:
                key = read()
                if key == 0: return result
                result[key] = read()
        raise ValueError((stream.tell(), tag))
    values = []
    while stream.tell() < len(data): values.append(read())
    names = values[-1]
    def rename(value):
        if isinstance(value, dict):
            return {names.get(k, str(k)): rename(v) for k, v in value.items()}
        return value
    return [rename(v) for v in values[:-1] if isinstance(v, dict)]

source = Path(sys.argv[1])
with zipfile.ZipFile(source) as z:
    output = {name: decode(z.read(name)) for name in z.namelist()}
source.with_suffix('.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
print('WINDOWS_DECODED', list(output))
