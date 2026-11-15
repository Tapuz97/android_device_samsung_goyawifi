"""Verify actual image APK icon aliases and all density pixels against source."""
from pathlib import Path
import hashlib,io,json,re,subprocess,zipfile
from PIL import Image
WORK=Path('/root/t110-lineage14-ui');SRC=Path('/root/t110-lineage14/android')
ART=WORK/'artifacts-icons-20261115'
manifest=json.loads((WORK/'icon-reference/port-manifest.json').read_text())
apks={
 'AudioFX':'priv-app/AudioFX/AudioFX.apk','Browser':'app/Jelly/Jelly.apk',
 'Calculator':'app/ExactCalculator/ExactCalculator.apk','Calendar':'app/Calendar/Calendar.apk',
 'Camera':'app/Camera2/Camera2.apk','Clock':'app/DeskClock/DeskClock.apk',
 'Contacts':'priv-app/Contacts/Contacts.apk','Email':'app/Email/Email.apk',
 'Files':'priv-app/DocumentsUI/DocumentsUI.apk','Gallery':'priv-app/Gallery2/Gallery2.apk',
 'Music':'priv-app/Eleven/Eleven.apk','Recorder':'priv-app/Recorder/Recorder.apk',
 'Settings':'priv-app/Settings/Settings.apk'}
DEST=ART/'icon-apk-verification';DEST.mkdir(exist_ok=True)
aapt=WORK/'out/host/linux-x86/bin/aapt'
results=[]
def parsed_manifest(text):
    stack=[];root=None
    for line in text.splitlines():
        depth=len(line)-len(line.lstrip())
        element=re.match(r'\s*E: ([\w-]+)',line)
        if element:
            item={'tag':element[1],'attrs':{},'children':[]}
            while stack and stack[-1][0]>=depth:stack.pop()
            if stack:stack[-1][1]['children'].append(item)
            else:root=item
            stack.append((depth,item));continue
        attribute=re.match(r'\s*A: ([\w:]+)(?:\([^)]*\))?=(.*)',line)
        if attribute and stack:
            value=attribute[2]
            literal=re.match(r'"([^"]*)"',value)
            stack[-1][1]['attrs'][attribute[1]]=literal[1] if literal else value
    assert root and root['tag']=='manifest'
    return root
def launcher_icons(text,canonical):
    manifest=parsed_manifest(text)
    app=next(x for x in manifest['children'] if x['tag']=='application')
    assert app['attrs'].get('android:icon')=='@'+canonical
    package=manifest['attrs']['package']
    def full(name):return package+name if name.startswith('.') else (name if '.' in name else package+'.'+name)
    activities={full(x['attrs']['android:name']):x for x in app['children'] if x['tag']=='activity'}
    found=[]
    for component in app['children']:
        if component['tag'] not in ('activity','activity-alias'):continue
        is_launcher=False
        for intent in component['children']:
            if intent['tag']!='intent-filter':continue
            actions=[x['attrs'].get('android:name') for x in intent['children'] if x['tag']=='action']
            categories=[x['attrs'].get('android:name') for x in intent['children'] if x['tag']=='category']
            is_launcher|='android.intent.action.MAIN' in actions and 'android.intent.category.LAUNCHER' in categories
        if not is_launcher:continue
        icon=component['attrs'].get('android:icon')
        if icon is None and component['tag']=='activity-alias':
            target=activities[full(component['attrs']['android:targetActivity'])]
            icon=target['attrs'].get('android:icon')
        icon=icon or app['attrs']['android:icon']
        assert icon=='@'+canonical,(component['attrs']['android:name'],icon,canonical)
        found.append(full(component['attrs']['android:name']))
    assert found
    return found
for app in manifest['apps']:
    rel=apks[app['label']];target=DEST/(app['label']+'.apk')
    subprocess.run(['debugfs','-R','dump -p /'+rel+' '+str(target),str(ART/'system.raw.img')],
                   check=True,capture_output=True)
    assert target.is_file(),rel
    assert hashlib.sha256(target.read_bytes()).digest()==hashlib.sha256((WORK/'out/target/product/goyawifi/system'/rel).read_bytes()).digest(),rel
    resources=subprocess.check_output([str(aapt),'dump','resources',str(target)],text=True)
    ids=re.findall(r'resource\s+(0x[0-9a-f]+)\s+\S+:mipmap/t110_modern_launcher\b',resources)
    assert len(set(ids))==1,(app['label'],ids)
    canonical=ids[0]
    with zipfile.ZipFile(target) as apk:
        assert apk.testzip() is None
        for old in app['original_icon_resources']:
            kind,name=old.split('/')
            assert 'res/'+kind+'-anydpi-v25/'+name+'.xml' not in apk.namelist()
        for density in ('mdpi','hdpi','xhdpi','xxhdpi','xxxhdpi'):
            name='res/mipmap-'+density+'-v4/t110_modern_launcher.png'
            compiled=Image.open(io.BytesIO(apk.read(name))).convert('RGBA')
            source=Image.open(SRC/app['retained_source_root']/('mipmap-'+density)/'t110_modern_launcher.png').convert('RGBA')
            assert compiled.size==source.size and compiled.tobytes()==source.tobytes(),(app['label'],density)
        manifest_xml=subprocess.check_output([str(aapt),'dump','xmltree',str(target),'AndroidManifest.xml'],text=True)
        launcher=launcher_icons(manifest_xml,canonical)
    results.append({'label':app['label'],'apk':rel,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                    'launcher_components':launcher,'resolved_icon_resource':canonical,'matching_density_images':5})
report={'status':'PASS_ACTUAL_IMAGE_ICON_PIXELS_AND_LAUNCHER_MANIFESTS','apps':results,
        'native_app_count':13,'density_images_checked':65,'android_api':25,
        'runtime_icon_pack_or_renderer_required':False}
digest=hashlib.sha256()
with (ART/'system.raw.img').open('rb') as image:
    for block in iter(lambda:image.read(8*1024*1024),b''):digest.update(block)
report['system_image_sha256']=digest.hexdigest()
(ART/'native-icon-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: 13 actual image APKs, 65 matching density images and native launcher manifest selection.')
