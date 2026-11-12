"""Make full replacement patches so repeated builds can verify applied state."""
from pathlib import Path
import difflib
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');t=Path('/root/t110-build/lineage20')
for base,output,repo,name in [
 ('0056-composer-t110-padded-portrait-scanout.patch','0064-composer-t110-cached-scanout-staging.patch','hardware/interfaces','graphics/composer/2.1/default/T110Framebuffer.cpp'),
 ('0053-renderengine-t110-oriented-window-bridge.patch','0065-renderengine-t110-reuse-idle-swap-spares.patch','frameworks/native','libs/renderengine/gl/T110EglWindow.cpp')]:
    old=(p/'patches'/base).read_text()
    diff=p/'patches'/output
    (p/'evidence/offline-v35'/(output+'.incremental')).write_text(diff.read_text())
    marker='diff --git a/'+name+' b/'+name+'\n'
    begin=old.index(marker);end=old.find('diff --git ',begin+len(marker))
    if end<0:end=len(old)
    content=(t/repo/name).read_text()
    full=marker+''.join(difflib.unified_diff([],content.splitlines(True),fromfile='/dev/null',tofile='b/'+name))
    diff.write_text(old[:begin]+full+old[end:],encoding='utf-8')
f=p/'scripts/build_system_image.sh';s=f.read_text()
for old,new in [('hardware/interfaces:0056-composer-t110-padded-portrait-scanout.patch','hardware/interfaces:0064-composer-t110-cached-scanout-staging.patch'),('frameworks/native:0053-renderengine-t110-oriented-window-bridge.patch','frameworks/native:0065-renderengine-t110-reuse-idle-swap-spares.patch')]:
    assert s.count("'"+new+"'")==1
    s=s.replace(" '"+new+"'",'').replace(old,new)
f.write_text(s,encoding='utf-8')
print('SUPERSEDING_PATCHES_READY')
