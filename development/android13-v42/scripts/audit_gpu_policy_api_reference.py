"""Record the audited existing compatibility contract in this fork's API33 reference.

This does not change effective runtime rules. It applies reviewed GPU, legacy
swapon and device-property hunks to four files, never skips checks and never
copies the public policy tree wholesale. Older API references remain untouched.
"""
from pathlib import Path
import hashlib,json,os,subprocess
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
root=Path('/root/t110-build/lineage20/system/sepolicy')
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
sha=lambda data:hashlib.sha256(data).hexdigest()
changes={
 'public/attributes':[(b'######################################\n# Attribute declarations\n#',b'# T110 stock GPU library. Only the device policy assigns this attribute.\nattribute t110_gpu_file_type;\n\n\n######################################\n# Attribute declarations\n#')],
 'public/domain.te':[(b'  -asec_public_file\n}:file execmod;',b'  -asec_public_file\n  -t110_gpu_file_type\n}:file execmod;'),
              (b'neverallow { domain -untrusted_app_25 -untrusted_app_27 } file_type:file execmod;',b'neverallow { domain -untrusted_app_25 -untrusted_app_27 } { file_type -t110_gpu_file_type }:file execmod;')],
 'private/access_vectors':[(b'\twatch_reads\n}',b'\twatch_reads\nifdef(`t110_legacy_swapon\', `\tswapon\')\n}')],
 'private/property_contexts':[(b'vibrator.adaptive_haptics.enabled u:object_r:adaptive_haptics_prop:s0 exact string\n',
 b'vibrator.adaptive_haptics.enabled u:object_r:adaptive_haptics_prop:s0 exact string\n\n# T110 engineering compatibility switches must be readable by native services.\nro.t110.legacy_processgroups u:object_r:exported_default_prop:s0 exact bool\nro.t110.legacy_usb u:object_r:exported_default_prop:s0 exact bool\nro.t110.legacy_gpu u:object_r:exported_default_prop:s0 exact bool\nro.t110.legacy_bpf u:object_r:exported_default_prop:s0 exact bool\n')],
}
record={}
for name,hunks in changes.items():
 baseline=subprocess.check_output(['git','-C',str(root),'show','HEAD:'+name])
 expected=baseline
 for old,new in hunks:
  assert expected.count(old)==1
  expected=expected.replace(old,new,1)
 actual=(root/name).read_bytes();assert actual==expected,('Additional unaudited policy changes',name)
 reference=root/'prebuilts/api/33.0'/name
 before=reference.read_bytes();assert before in [baseline,expected],'API reference has unrelated changes'
 reference.write_bytes(expected)
 record[name]=dict(baseline_sha256=sha(baseline),effective_policy_before_and_after_sha256=sha(actual),reference_sha256=sha(expected),hunks=len(hunks))
subprocess.run(['git','-C',str(root),'diff','--check'],check=True)
for directory in ['public','private']:
 subprocess.run(['diff','-r','-q','-x','bug_map',str(root/directory),str(root/'prebuilts/api/33.0'/directory)],check=True)
diff=subprocess.check_output(['git','-C',str(root),'diff','--']+['prebuilts/api/33.0/'+name for name in changes])
(p/'patches/0106-sepolicy-record-existing-t110-gpu-api-contract.patch').write_bytes(diff)
(p/'evidence/ui-system-hang-20261112/gpu-api-reference-audit.json').write_text(json.dumps(dict(status='EXACT_EXISTING_CONTRACT_RECORDED',files=record,effective_policy_changed=False,checks_disabled=False,other_api_versions_changed=False),indent=2)+'\n')
print('All four existing compatibility definitions audited; complete public/private freeze comparison passes; effective policy unchanged')
