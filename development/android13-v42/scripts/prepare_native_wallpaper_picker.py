"""Adapt the existing wallpaper picker bitmap allocation on the T110 only."""
from pathlib import Path
import difflib,json,subprocess,hashlib

p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
repo=Path('/root/t110-build/lineage20/packages/apps/WallpaperPicker2')
changes={
 'src/com/android/wallpaper/asset/StreamableAsset.java':(
    '            options.inPreferredConfig = Config.HARDWARE;',
    '''            // Software Canvas windows need CPU-readable preview/crop bitmaps.
            options.inPreferredConfig = "t110_bringup".equals(android.os.Build.DEVICE)
                    ? Config.ARGB_8888 : Config.HARDWARE;'''),
 'src/com/android/wallpaper/asset/WallpaperGlideModule.java':(
    '''        builder.setDefaultRequestOptions(
                new RequestOptions().format(DecodeFormat.PREFER_ARGB_8888));''',
    '''        RequestOptions options = new RequestOptions().format(DecodeFormat.PREFER_ARGB_8888);
        if ("t110_bringup".equals(android.os.Build.DEVICE)) {
            options = options.disallowHardwareConfig();
        }
        builder.setDefaultRequestOptions(options);'''),
}
patch=[];records={}
for name,(before,after) in changes.items():
    old=subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+name],text=True)
    assert old.count(before)==1,name
    new=old.replace(before,after)
    assert (repo/name).read_text() in [old,new],name
    patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),'a/'+name,'b/'+name))
    records[name]={'before_sha256':hashlib.sha256(old.encode()).hexdigest(),'after_sha256':hashlib.sha256(new.encode()).hexdigest()}
target=p/'patches/0075-wallpaperpicker-t110-readable-bitmaps.patch'
target.write_bytes(''.join(patch).encode())
if subprocess.run(['git','-C',str(repo),'apply','--reverse','--check',str(target)],capture_output=True).returncode:
    subprocess.run(['git','-C',str(repo),'apply','--check',str(target)],check=True)
    subprocess.run(['git','-C',str(repo),'apply',str(target)],check=True)
# Drop only the obsolete launcher routing overlay left by the previous cp -a sync.
overlay=Path('/root/t110-build/lineage20/device/samsung/t110_bringup/overlay/packages/apps/Trebuchet/res/values/config.xml')
if overlay.exists():
    text=overlay.read_text()
    assert 'wallpaper_picker_package' in text and 'org.lineageos.t110.wallpapers' in text
    overlay.unlink()
e=p/'evidence/offline-v39';e.mkdir(exist_ok=True)
(e/'picker-source.json').write_text(json.dumps({'status':'APPLIED','files':records,'features_removed':[]},indent=2)+'\n')
print('NATIVE_WALLPAPER_PICKER_SOURCE_READY')
