"""Annotate Thumb PC-relative string loads in the retained stock HAL disassembly."""
from pathlib import Path
import re, struct, sys
root=Path('/root/t110-lineage14/reference')
b=Path(sys.argv[1]).read_bytes() if len(sys.argv)>1 else (root/'stock-ani7/extracted/lib/hw/audio.primary.mrvl.so').read_bytes()
p=Path(sys.argv[2]) if len(sys.argv)>2 else root/'hal-abi/stock-audio-output-parameters.txt'
registers={}
lines=[]
for line in p.read_text().splitlines():
    match=re.match(r'\s*([0-9a-f]+):.*\bldr(?:\.w)?\s+(\w+), \[pc, #[0-9]+\].*; \(?([0-9a-f]+)',line)
    if match:
        addr,reg,pool=match.groups(); registers[reg]=struct.unpack_from('<i',b,int(pool,16))[0]
    add=re.match(r'\s*([0-9a-f]+):.*\badd\s+(\w+), pc',line)
    if add and add[2] in registers:
        target=registers.pop(add[2])+int(add[1],16)+4
        if 0<=target<len(b):
            text=b[target:b.find(b'\0',target)]
            if 2<len(text)<180 and all(32<=x<127 for x in text):
                line+='  // '+hex(target)+' '+text.decode()
    lines.append(line)
out=p.with_suffix('.annotated.txt');out.write_text('\n'.join(lines)+'\n')
print(out)
