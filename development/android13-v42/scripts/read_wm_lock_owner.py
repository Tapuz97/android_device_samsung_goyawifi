from pathlib import Path
import re
p=Path(__file__).resolve().parents[1];text=(p/'evidence/ui-system-hang-20261112/trace_03').read_bytes().decode(errors='replace').replace('\r','')
for tid in [129]:
 m=re.search(r'^"[^\n]+\btid='+str(tid)+r'\b[^\n]*\n',text,re.M);assert m
 rest=text[m.end():];n=re.search(r'^"[^\n]+\btid=\d+',rest,re.M);block=text[m.start():m.end()+n.start() if n else m.end()+6000]
 print('\n'.join(block.splitlines()[:75]))
