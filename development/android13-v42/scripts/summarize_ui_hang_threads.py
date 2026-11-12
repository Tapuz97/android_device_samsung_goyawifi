from pathlib import Path
import re
p=Path(__file__).resolve().parents[1];e=p/'evidence/ui-system-hang-20261112'
for f in [*e.glob('anr_*'),*e.glob('trace_*')]:
 text=f.read_bytes().decode('utf-8',errors='replace').replace('\r','');print('\nFILE',f.name)
 print('Processes:',', '.join(dict.fromkeys(re.findall(r'Cmd line: (.*)',text))))
 for match in re.finditer(r'^"(?:main|android\.ui|android\.fg|RenderThread)"[^\n]*\n',text,re.M):
  next_thread=re.search(r'^"[^\n]+".*\btid=\d+',text[match.end():],re.M)
  end=match.end()+next_thread.start() if next_thread else match.end()+5000
  block=text[match.start():end];print('\n'.join(block.splitlines()[:45]))
