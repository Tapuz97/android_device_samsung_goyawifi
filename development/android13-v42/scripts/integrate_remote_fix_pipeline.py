"""Wire verified source fixes into the normal build path; no firmware writes."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
f=p/'scripts/build_system_image.sh';s=f.read_text()
anchor="'frameworks/base:0076-systemui-t110-finite-notification-clips.patch'; do"
if anchor in s:
    s=s.replace(anchor,"'frameworks/base:0076-systemui-t110-finite-notification-clips.patch' 'lineage-sdk:0077-lineage-sdk-t110-nonblocking-hardware-probes.patch' 'frameworks/native:0078-gralloc-t110-initialize-import-only-clients.patch'; do")
    f.write_text(s,newline='\n')
else:assert '0077-lineage-sdk' in s and '0078-gralloc' in s
f=p/'scripts/build_remote_ion_kernel.sh';s=f.read_text()
helper=p/'scripts/prepare_ion_map_kernel.py'
if 'prepare_ion_map_kernel.py' not in s:
    start=s.index('python3 - "$project" <<\'PY\'\n');end=s.index('\nPY\n',start)
    assert helper.exists()
    s=s[:start]+'python3 "$project/scripts/prepare_ion_map_kernel.py" "$project"\n'+s[end+4:];f.write_text(s,newline='\n')
else:assert helper.exists()
f=p/'scripts/build_display_i2c_kernel.sh';s=f.read_text();anchor='python3 "$project/scripts/prepare_touch_charge_kernel.py"\n'
assert anchor in s
if 'prepare_ion_map_kernel.py' not in s:s=s.replace(anchor,anchor+'python3 "$project/scripts/prepare_ion_map_kernel.py" "$project"\n');f.write_text(s,newline='\n')
print('NORMAL_SYSTEM_AND_KERNEL_BUILD_PATHS_UPDATED')
