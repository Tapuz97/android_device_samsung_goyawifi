from pathlib import Path
import subprocess,shutil,json,hashlib
audit=Path('/root/t110-android13-audit');android=Path('/root/t110-android13/android')
out=audit/'device/development/android13-audit-20261114/phase3';out.mkdir(exist_ok=True)
patchdir=out/'complete-project-deltas';patchdir.mkdir(exist_ok=True)
names=('bionic','frameworks/native','frameworks/base','hardware/interfaces','system/sepolicy')
records=[]
for name in names:
 p=android/name
 patch=subprocess.check_output(['git','-C',str(p),'diff','--binary','--full-index','HEAD'])
 subprocess.run(['git','-C',str(p),'diff','--check'],check=True)
 dest=patchdir/(name.replace('/','__')+'.patch');dest.write_bytes(patch)
 records.append(dict(project=name,base=subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip(),patch=dest.name,sha256=hashlib.sha256(patch).hexdigest()))
(out/'projects.json').write_text(json.dumps(records,indent=2)+'\n')
device=android/'device/samsung/t110_bringup'
# The original product is in the private source capsule; these are the changed source inputs.
product=out/'product';product.mkdir(exist_ok=True)
for name in ('t110_system.mk','sepolicy/t110_audio.te','sepolicy/file_contexts','sepolicy/genfs_contexts'):
 p=product/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(device/name,p)
audio=product/'audio';audio.mkdir(exist_ok=True)
for p in (device/'audio').iterdir():
 if p.is_file() and p.suffix in ('.h','.cpp','.md','.rc','.mk','.bp','.xml','.json'):shutil.copy2(p,audio/p.name)
shutil.copy2(audit/'vendor-audio-packaging.json',out/'vendor-audio-inputs.json')
shutil.copy2(audit/'audio-load-probe.json',out/'loader-diagnostic.json')
tools=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/android13-audit')
for name in ('restore_full_android13.py','integrate_full_source.py','package_vendor_audio.py','prepare_audio_loader_root.py','run_audio_load_probe.py','AudioLoadProbe.c','build_full_components.sh','export_phase3_source.py'):
 shutil.copy2(tools/name,out/name)
(out/'RESTORE-NOTES.md').write_text('''# Full build integration checkpoint

The five complete-project-deltas replace the corresponding original capsule
patches when restoring from the exact pinned upstream HEADs in projects.json.
They include the old source changes plus the phase1/2 graphics fixes and phase3
linker/policy changes. Do not apply them after the old patches, or apply the
earlier incremental patches again. All other capsule project deltas and original
untracked files remain prerequisites.

product/ contains changed source/configuration inputs for the original custom
product. Binary vendor inputs and the stock configuration payload are generated
locally by package_vendor_audio.py from the verified stock image; they are not
published here. Keep original module assets from the private restoration capsule.
The original graphics/radio/navigation source is preserved.

The loader diagnostic is real Android Bionic running under ARM QEMU, with no
hardware access. Its process temporarily sets target SDK22 to diagnose dependency
resolution before the new exact-libippsp textrel exception can be exercised in
production. It has no production namespace configuration; do not report that
diagnostic as a production audio-HAL or SELinux test. Full build results are
recorded separately after the build exits.

REA's pwntools ELF provider could not read this artifact on Windows (Linux x64
host required). ELF/dependency work used ordinary WSL readelf/patchelf tools and
the exact ALSA1.0.23 upstream source alongside real stock-binary loader checks.
No REA retained Evidence or successful native analysis is claimed.
''')
print('Preserved full project deltas and generated product source; vendor binaries excluded.')
