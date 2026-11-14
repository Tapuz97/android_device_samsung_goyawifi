from pathlib import Path
import hashlib
import json
import shutil

audit = Path('/root/t110-android13-audit')
tools = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/android13-audit')
out = audit / 'device/development/android13-audit-20261114/phase4'
out.mkdir(exist_ok=True)
names = ('PHASE4-IN-PROGRESS.md', 'build_complete_image.sh', 'prepare_complete_image_geometry.py',
         'BuildCandidatePropertyInfo.cpp', 'CandidateNamespaceProbe.c', 'build_namespace_tools.py',
         'inspect_android13_boot.py', 'export_phase4_source.py')
for name in names:
    shutil.copy2(tools / name, out / name)
product = Path('/root/t110-android13/android/device/samsung/t110_bringup')
(out / 'product').mkdir(exist_ok=True)
shutil.copy2(product / 'BoardConfig.mk', out / 'product/BoardConfig.mk')
for name in ('complete-image-geometry.json','preserved-android13-boot.json'):
    if (audit / name).is_file(): shutil.copy2(audit / name, out / name)
if (audit / 'namespace-tools/toolchain.json').is_file():
    shutil.copy2(audit / 'namespace-tools/toolchain.json', out / 'namespace-toolchain.json')
records=[]
for p in sorted(out.rglob('*')):
    if p.is_file() and p.name != 'source-checkpoint.json':
        records.append(dict(path=str(p.relative_to(out)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(out / 'source-checkpoint.json').write_text(json.dumps(dict(
    base='ce73cdbb2644e1919645068853657a5b9c3efa3c',
    prerequisites='phase3 complete-project-deltas, project-additions and original private restoration capsule',
    status='FULL_IMAGE_AND_PRODUCTION_NAMESPACE_PENDING',files=records, flashed=False),indent=2)+'\n')
print('Exported phase4 source/geometry/tool checkpoint without altering the phase3 backup.')
