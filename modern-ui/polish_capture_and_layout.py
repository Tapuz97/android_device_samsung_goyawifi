"""Use Nougat's existing legacy capture path and finish the responsive layout."""
from pathlib import Path
import hashlib,json,shutil,subprocess
helper=Path(__file__).with_name('apply_modern_ui.py').read_text()
exec(helper[:helper.index("FW='frameworks/base/'")])
FW='frameworks/base/';UI=FW+'packages/SystemUI/';LAUNCH='packages/apps/Trebuchet/'

# Preserve the complete pre-change native bring-up, not only the edited file.
manifest=WORK/'baseline/project-manifest.json'
baseline=json.loads(manifest.read_text())
project='frameworks/native';repo=SRC/project
if not any(item['project']==project for item in baseline['projects']):
    dest=WORK/'baseline'/project;dest.mkdir(parents=True,exist_ok=True)
    patch=subprocess.check_output(['git','-C',str(repo),'diff','--binary','HEAD'])
    (dest/'bringup-baseline.patch').write_bytes(patch)
    additions=[]
    for raw in subprocess.check_output(['git','-C',str(repo),'ls-files','--others','--exclude-standard','-z']).split(b'\0'):
        if not raw:continue
        rel=raw.decode();source=repo/rel
        if source.is_file():
            target=dest/'untracked'/rel;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
            additions.append({'path':rel,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    baseline['projects'].append({'project':project,
        'upstream_head':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
        'baseline_patch_sha256':hashlib.sha256(patch).hexdigest(),'additions':additions})
    manifest.write_text(json.dumps(baseline,indent=2)+'\n')

device='device/samsung/goyawifi/device.mk'
line='PRODUCT_PROPERTY_OVERRIDES += ro.bq.gpu_to_cpu_unsupported=1'
if line not in read(device):
    save(device,read(device)+'\n# Use Nougat\'s native readPixels capture path for the Vivante GC1000.\n'+line+'\n')

# Bitmap captures already request this path. Surface-consuming captures also
# need it; keep every existing SurfaceFlinger permission/secure-layer check.
native='frameworks/native/libs/gui/SurfaceComposerClient.cpp'
edit(native,'#include <stdint.h>','#include <stdint.h>\n#include <cutils/properties.h>')
edit(native,'''    return s->captureScreen(display, producer, sourceCrop,
            reqWidth, reqHeight, minLayerZ, maxLayerZ, useIdentityTransform,
            ISurfaceComposer::eRotateNone, SS_CPU_CONSUMER);''',
'''    bool useReadPixels = SS_CPU_CONSUMER;
#ifdef T110_MRVL_LEGACY
    useReadPixels = useReadPixels || property_get_bool("ro.bq.gpu_to_cpu_unsupported", false);
#endif
    return s->captureScreen(display, producer, sourceCrop,
            reqWidth, reqHeight, minLayerZ, maxLayerZ, useIdentityTransform,
            ISurfaceComposer::eRotateNone, useReadPixels);''')

# The old landscape shade was only544dp wide. Four horizontal tiles need the
# actual display width; use the same native match-parent contract as portrait.
resource(UI+'res/values-w550dp-land/dimens.xml','dimen','notification_panel_width','@dimen/match_parent')
path=UI+'res/values-sw600dp-land/t110_modern.xml'
text=read(path)
if 'notification_panel_width' not in text:
    save(path,text.replace('</resources>','<dimen name="notification_panel_width">@dimen/match_parent</dimen></resources>'))
edit(UI+'res/layout/qs_tile_label.xml','android:ellipsize="end"',
     'android:ellipsize="end" android:breakStrategy="simple" android:hyphenationFrequency="none"')

# Use existing native preferences. Keep the compact toggle and every stock
# tile available, while choosing appropriate defaults for a Wi-Fi-only tablet.
resource(LAUNCH+'res/values/preferences_defaults.xml','bool','preferences_interface_drawer_compact_default','true')
resource(UI+'res/values/config.xml','string','quick_settings_tiles_default',
         '\n        wifi,battery,dnd,rotation,bt,airplane\n    ')
print('Preserved native baseline; enabled standard capture fallback, responsive landscape and native compact defaults.')
