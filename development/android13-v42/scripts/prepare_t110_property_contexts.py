from pathlib import Path
import difflib
p=Path('/root/t110-build/lineage20/system/sepolicy/private/property_contexts')
before=p.read_text()
assert 'ro.t110.legacy_bpf ' not in before
names=['legacy_processgroups','legacy_usb','legacy_gpu','legacy_bpf']
after=before+'\n# T110 engineering compatibility switches must be readable by native services.\n'+''.join('ro.t110.'+name+' u:object_r:exported_default_prop:s0 exact bool\n' for name in names)
p.write_text(after)
patch=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/patches/0027-sepolicy-t110-compat-property-contexts.patch')
patch.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/private/property_contexts',tofile='b/private/property_contexts')))
print('Added explicit contexts for four read-only compatibility flags')
