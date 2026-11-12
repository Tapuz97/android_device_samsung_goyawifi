from pathlib import Path
import json,subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
e=p/'evidence/offline-v30';s=Path('/root/t110-build/portrait-roundtrip')
cmd=['g++','-std=c++17','-O1','-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',str(p/'scripts/test_portrait_scanout.cpp'),'-o',str(s/'scanout-test')]
r=subprocess.run(cmd,capture_output=True,text=True);(e/'scanout-compile.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
r=subprocess.run([str(s/'scanout-test')],capture_output=True,text=True);(e/'scanout-regression.log').write_text(r.stdout+r.stderr);assert r.returncode==0 and 'runtime error:' not in r.stderr,r.stdout+r.stderr
native=Path('/root/t110-build/lineage20/hardware/interfaces')
subprocess.run(['git','apply','--reverse','--check',str(p/'patches/0055-composer-t110-natural-portrait-scanout.patch')],cwd=native,check=True)
assert (p/'work/T110Framebuffer.cpp').read_bytes()==(native/'graphics/composer/2.1/default/T110Framebuffer.cpp').read_bytes()
assert (p/'work/T110Scanout.h').read_bytes()==(native/'graphics/composer/2.1/default/T110Scanout.h').read_bytes()
product=(p/'work/device/samsung/t110_bringup/t110_system.mk').read_text();assert 'primary_display_orientation=ORIENTATION_0' in product
fb=(p/'work/T110Framebuffer.cpp').read_text()
old=(e/'T110Framebuffer.cpp.before').read_text()
assert fb[fb.index('int enableScreen('):fb.index('int closeDevice(')]==old[old.index('int enableScreen('):old.index('int closeDevice(')]
(e/'regressions.json').write_text(json.dumps(dict(status='PASS',pixel_mapping='All 614400 pixels, three source strides, two destination pitches, both pages and channel orders',bounds='Truncation, padding and canaries, invalid page, null, overflow inputs',sanitizers='ASan and UBSan nonrecovering',power_fix_retained=True,android_boots=0,limits='Physical UI and touch still require full ROM validation'),indent=2)+'\n')
print(r.stdout)
