from pathlib import Path
import hashlib
import json
import shutil

audit = Path('/root/t110-android13-audit')
tools = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/android13-audit')
out = audit / 'device/development/android13-audit-20261114/phase4'
out.mkdir(exist_ok=True)
names = ('PHASE4-IN-PROGRESS.md', 'build_complete_image.sh', 'run_complete_candidate_gates.sh', 'prepare_complete_image_geometry.py',
         'BuildCandidatePropertyInfo.cpp', 'CandidateNamespaceProbe.c', 'ProductionAudioProbe.c', 'build_namespace_tools.py', 'restore_pinned_webview.py',
         'inspect_android13_boot.py', 'verify_kernel_carryover.py', 'verify_complete_image.py',
         'run_production_namespace_checks.py', 'carry_gpu_node_fix.py',
         'package_android13_candidate_boot.py', 'check_complete_image_policy.py',
         'backup_complete_candidate.py', 'export_phase4_source.py')
for name in names:
    shutil.copy2(tools / name, out / name)
product = Path('/root/t110-android13/android/device/samsung/t110_bringup')
(out / 'product').mkdir(exist_ok=True)
for name in ('BoardConfig.mk','graphics.mk','graphics/ueventd.t110.rc','sepolicy/file_contexts'):
    target=out/'product'/name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(product/name,target)
for name in ('complete-image-geometry.json','preserved-android13-boot.json','kernel-carryover-verification.json',
             'complete-image-verification.json','production-namespace-verification.json','pinned-webview-verification.json'):
    if (audit / name).is_file(): shutil.copy2(audit / name, out / name)
for name in ('gpu-node-carryover.json','candidate-boot-verification.json','complete-image-policy-verification.json'):
    if (audit/name).is_file():shutil.copy2(audit/name,out/name)
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
