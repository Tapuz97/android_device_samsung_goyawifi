"""Verify contents extracted from the actual final ext4 artifact, not just its staging tree."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
BASE=Path('/root/t110-lineage14');ANDROID=BASE/'android';OUT=ANDROID/'out/target/product/goyawifi'
ART=BASE/'artifacts/lineage14-first-build';IMAGE=ART/'system.raw.img'
inputs=json.loads((ANDROID/'device/samsung/goyawifi/vendor-inputs.json').read_text())['files']
paths={str(Path(x['destination']).relative_to('/system')) for x in inputs}
paths.update(['build.prop','bin/t110_stage','bin/linker','lib/libEGL.so','lib/libui.so',
 'lib/libutils.so','lib/libbinder.so','lib/libcutils.so','lib/libcamera_client.so',
 'lib/libandroid_servers.so','lib/libaudioflinger.so','lib/libsurfaceflinger.so','vendor/lib/modules/galcore.ko',
 'etc/audio_policy.conf','usr/keylayout/gpio-keys.kl','usr/keylayout/sec_touchscreen.kl',
 'priv-app/Settings/Settings.apk','priv-app/CMParts/CMParts.apk','priv-app/SystemUI/SystemUI.apk',
 'priv-app/Trebuchet/Trebuchet.apk','app/LatinIME/LatinIME.apk',
 'priv-app/WallpaperCropper/WallpaperCropper.apk','app/LiveWallpapersPicker/LiveWallpapersPicker.apk'])
report=[]
with tempfile.TemporaryDirectory(prefix='t110-final-ext4-') as tmp:
 for index,name in enumerate(sorted(paths)):
    source=OUT/'system'/name
    assert source.is_file(), 'Required installed file missing: '+name
    target=Path(tmp)/str(index)
    result=subprocess.run(['debugfs','-R','dump -p /'+name+' '+str(target),str(IMAGE)],capture_output=True,text=True)
    assert target.is_file(), 'Image extraction failed: '+name+' '+result.stderr
    expected=hashlib.sha256(source.read_bytes()).hexdigest()
    actual=hashlib.sha256(target.read_bytes()).hexdigest()
    assert expected==actual, 'Image content mismatch: '+name
    if name=='build.prop':
        p=dict(line.split('=',1) for line in target.read_text().splitlines() if '=' in line and not line.startswith('#'))
        assert p['ro.build.version.release']=='7.1.2' and p['ro.build.version.sdk']=='25'
    report.append({'path':name,'sha256':actual,'bytes':target.stat().st_size})
record={'status':'PASS','scope':'Actual final ext4 content matches installed final build; Android7 properties, critical platform/apps, all selected vendor inputs','files':report}
(ART/'image-content-verification.json').write_text(json.dumps(record,indent=2)+'\n')
print('Verified',len(report),'files extracted from the actual final ext4 image.')
