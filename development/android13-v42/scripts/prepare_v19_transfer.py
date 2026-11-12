"""Prepare the checked compressed transfer for v19 with the current installed BOOT guard."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
s=(p/'scripts/stage_v18_system.py').read_text()
s=s.replace('v18','v19').replace('evidence/offline-v27/contents.json','evidence/offline-v29/contents.json')
s=s.replace('evidence/offline-v26/boot-verification.json','evidence/offline-v28/boot-verification.json')
s=s.replace('f3f30815e1823ea4425847e3020a7d4b','942182cefec3cb7666096499220789d0')
(p/'scripts/stage_v19_system.py').write_text(s)
print('Prepared v19 transfer; not executed.')
