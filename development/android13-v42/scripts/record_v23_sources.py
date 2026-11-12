from pathlib import Path
import hashlib,json,subprocess
base=Path('/root/t110-build/lineage20')
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
entries=[]
for repo,name,files in [
    ('frameworks/native','0038-renderengine-t110-egl-window-bridge.patch',[
        'libs/renderengine/gl/GLESRenderEngine.cpp','libs/renderengine/gl/GLESRenderEngine.h',
        'libs/renderengine/gl/T110EglWindow.cpp','libs/renderengine/gl/T110EglWindow.h',
        'libs/renderengine/gl/T110WindowSlots.h','libs/renderengine/Android.bp']),
    ('art','0039-art-zygote-visibility-checkpoint-lock.patch',['runtime/runtime.cc'])]:
    patch=project/'patches'/name
    subprocess.run(['git','apply','--reverse','--check',str(patch)],cwd=base/repo,check=True)
    entries.append(dict(repo=repo,base_commit=subprocess.check_output(
        ['git','rev-parse','HEAD'],cwd=base/repo,text=True).strip(),patch=name,
        patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),
        sources={f:hashlib.sha256((base/repo/f).read_bytes()).hexdigest() for f in files}))
report=dict(build_log='system-image-20261106T175133Z.log',build_exit=0,sources=entries,
    superseded_patch='0037-renderengine-t110-resolve-before-handoff.patch',
    hardware_access=False,validation_notes='Offline build and host contracts; no device or emulator boot')
(project/'evidence/offline-v23/source-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
print('Source hashes and clean patch reversal verified')
