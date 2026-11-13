"""Publishable source snapshot only; never copy captures or private vendor blobs."""
from pathlib import Path
import shutil
base = Path('/root/t110-lineage14')
device = base/'android/device/samsung/goyawifi'
records = base/'records/source'
local = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
for source in records.glob('*.patch'):
    shutil.copy2(source, device/'compat-patches'/source.name)
for name in ('projects.json', 'pinned-manifest.xml'):
    shutil.copy2(records/name, device/'compat-patches'/name)
if (records/'untracked').exists():
    shutil.copytree(records/'untracked',device/'compat-patches/untracked',dirs_exist_ok=True)
shutil.copy2(local/'FUNCTIONAL-CHECKS-LINEAGE14.md',device/'docs/FUNCTIONAL-PASS-20261114.md')
shutil.copy2(local/'scripts/verify_final_image.py',device/'tools/verify_final_image.py')
shutil.copy2(local/'scripts/package_lineage14.py',device/'tools/package_lineage14.py')
for name in ('fix_functional_pass.py','restore_camera_ion_allocator.py',
             'restore_netd_uid_abi.py','fix_camera_window_detach.py',
             'fix_camera_encoder_access.py','fix_video_recording.py',
             'fix_audio_input_lifecycle.py','fix_audio_codec_dependency.py',
             'fix_audio_output_routing.py','integrate_vendor.py','add_audio_routing.py',
             'alsa_control_probe.c','annotate_audio_literals.py','extract_stock_alsa.py',
             'fix_recorder_file_failure.py','verify_vendor_elf.py','export_lineage14_source.py',
             'verify_recorder_wav.py'):
    shutil.copy2(local/'scripts'/name,device/'tools'/name)
print('Exported reviewed platform patches, verification tool and functional record.')
checklist = device/'docs/FUNCTIONAL-TESTS-LINEAGE14.md'
s = checklist.read_text()
notice = '\nLatest measured results: [functional pass, 2026-11-14](FUNCTIONAL-PASS-20261114.md).\nHardware passes below are limited to the observations stated there.\n'
if notice not in s:
    s = s.replace('# Lineage14 first full-ROM functional checks\n', '# Lineage14 first full-ROM functional checks\n'+notice)
statuses = {
    'Wi-Fi': 'PASS enable/scan/join/DNS/HTTPS, one sleep reconnect and media-build reboot',
    'Bluetooth': 'PASS toggle/discovery/pairing/OPP transfer; other profiles unverified',
    'Camera': 'PASS preview/stills/reopen; video PARTIAL, low FPS and audio retest pending',
    'Audio output': 'PARTIAL: installed speaker tone owner-confirmed clear; headphones/volume tests pending',
    'Audio input': 'PARTIAL: installed13s non-silent WAV and clean stop; speech quality/accessories pending',
    'Sleep/wake': 'PASS one unplugged131s kernel suspend with owner-confirmed display/touch; before media update',
    'Keyboard/search': 'PASS Settings search results and navigation; physical keyboard typing pending',
}
lines=[]
for line in s.splitlines():
    for area,status in statuses.items():
        if line.startswith('| '+area+' |'):
            columns=line.split('|'); columns[-2]=' '+status+' '; line='|'.join(columns)
    lines.append(line)
checklist.write_text('\n'.join(lines)+'\n')
notice='\nLatest media and suspend evidence: [2026-11-14](MEDIA-SUSPEND-CHECKS-20261114.md).\n'
s=checklist.read_text()
if notice not in s:checklist.write_text(s+notice)
