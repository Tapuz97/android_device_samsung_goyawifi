"""Adapt the proven compressed transfer for the verified v18/existing-v26 pair."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
source=(p/'scripts/stage_v17_system.py').read_text()
source=source.replace('v17','v18')
source=source.replace("project/'artifacts/android13-full-v26/system-pair.json'", "source.parent/'rom-pair.json'")
source=source.replace("project/'evidence/offline-v26/contents.json'", "project/'evidence/offline-v27/contents.json'")
source=source.replace('3f507c549441bb54e027cbb4ed20837c','f3f30815e1823ea4425847e3020a7d4b')
assert "source.parent/'rom-pair.json'" in source
assert "project/'evidence/offline-v26/boot-verification.json'" in source
target=p/'scripts/stage_v18_system.py'
assert not target.exists()
target.write_text(source)
print(target)
