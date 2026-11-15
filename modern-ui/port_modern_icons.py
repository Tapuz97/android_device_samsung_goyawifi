"""Flatten official adaptive-icon layers into native API25 launcher resources.

Art remains upstream Lineage art. SVG is an intermediate build representation,
not a runtime renderer or a replacement icon-pack implementation.
"""
from pathlib import Path
import base64, copy, hashlib, io, json, math
import re
import xml.etree.ElementTree as ET
import cairosvg
from PIL import Image, ImageDraw, ImageFont
helper=Path(__file__).with_name('apply_modern_ui.py').read_text()
exec(helper[:helper.index("FW='frameworks/base/'")])
ROOT=WORK/'icon-reference';UP=ROOT/'upstream'
RENDER=ROOT/'rendered';RENDER.mkdir(exist_ok=True)
A='{http://schemas.android.com/apk/res/android}'
S='http://www.w3.org/2000/svg'
ET.register_namespace('',S)
def node(parent,tag,attrs=None):return ET.SubElement(parent,'{'+S+'}'+tag,attrs or {})
def attr(e,k,default=None):return e.get(A+k,default)
def color(raw):
    assert raw.startswith('#'),raw
    if len(raw)==9:return '#'+raw[3:],int(raw[1:3],16)/255
    assert len(raw) in (4,7),raw
    return raw,1.0
sequence=0
def ident():
    global sequence
    sequence+=1
    return 'r'+str(sequence)
def gradient(path,defs):
    value=next((x for x in path.iter() if x.tag=='gradient'),None)
    if value is None:return None
    gid=ident();typ=attr(value,'type','linear')
    if typ=='radial':
        g=node(defs,'radialGradient',{'id':gid,'gradientUnits':'userSpaceOnUse',
            'cx':attr(value,'centerX'),'cy':attr(value,'centerY'),'r':attr(value,'gradientRadius')})
    else:
        assert typ=='linear',typ
        g=node(defs,'linearGradient',{'id':gid,'gradientUnits':'userSpaceOnUse',
            'x1':attr(value,'startX','0'),'y1':attr(value,'startY','0'),
            'x2':attr(value,'endX','0'),'y2':attr(value,'endY','0')})
    modes={'clamp':'pad','repeat':'repeat','mirror':'reflect'}
    g.set('spreadMethod',modes[attr(value,'tileMode','clamp')])
    stops=list(value)
    assert stops
    for item in stops:
        rgb,alpha=color(attr(item,'color'))
        node(g,'stop',{'offset':attr(item,'offset'),'stop-color':rgb,'stop-opacity':str(alpha)})
    return 'url(#'+gid+')'
def children(xml,parent,defs):
    current=parent
    for item in xml:
        tag=item.tag.split('}')[-1]
        if tag=='group':
            px=attr(item,'pivotX','0');py=attr(item,'pivotY','0')
            tx=attr(item,'translateX','0');ty=attr(item,'translateY','0')
            t='translate(%s,%s) rotate(%s) scale(%s,%s) translate(%s,%s)'%(
                float(px)+float(tx),float(py)+float(ty),attr(item,'rotation','0'),
                attr(item,'scaleX','1'),attr(item,'scaleY','1'),-float(px),-float(py))
            children(item,node(current,'g',{'transform':t}),defs)
        elif tag=='clip-path':
            cid=ident();clip=node(defs,'clipPath',{'id':cid})
            node(clip,'path',{'d':attr(item,'pathData'),'clip-rule':attr(item,'fillType','nonZero').replace('nonZero','nonzero').replace('evenOdd','evenodd')})
            current=node(current,'g',{'clip-path':'url(#'+cid+')'})
        elif tag=='path':
            assert attr(item,'trimPathStart','0') in ('0','0.0')
            assert attr(item,'trimPathEnd','1') in ('1','1.0')
            p=node(current,'path',{'d':attr(item,'pathData')})
            rgb,alpha=color(attr(item,'fillColor','#00000000'))
            fill=gradient(item,defs)
            p.set('fill',fill or rgb)
            p.set('fill-opacity',str(float(attr(item,'fillAlpha','1'))*(1 if fill else alpha)))
            p.set('fill-rule',attr(item,'fillType','nonZero').replace('nonZero','nonzero').replace('evenOdd','evenodd'))
            if attr(item,'strokeColor'):
                rgb,alpha=color(attr(item,'strokeColor'))
                p.set('stroke',rgb);p.set('stroke-opacity',str(alpha*float(attr(item,'strokeAlpha','1'))))
                p.set('stroke-width',attr(item,'strokeWidth','0'))
                p.set('stroke-linecap',attr(item,'strokeLineCap','butt'))
                p.set('stroke-linejoin',attr(item,'strokeLineJoin','miter'))
        else:raise AssertionError('Unsupported vector node '+tag)
def layer(repo,name,svg,defs):
    root=UP/repo
    paths=[root/'res/drawable'/name,root/'app/src/main/res/drawable'/name]
    p=next((p for p in paths if p.is_file()),None)
    assert p,(repo,name)
    vector=ET.parse(p).getroot()
    assert vector.tag=='vector'
    assert attr(vector,'viewportWidth')=='108' and attr(vector,'viewportHeight')=='108',p
    group=node(svg,'g',{'opacity':attr(vector,'alpha','1')})
    children(vector,group,defs)
def binary(name,data):
    target=SRC/name
    if target.exists() and target.read_bytes()==data:return
    if name not in files:
        if target.exists():
            old=target.read_bytes();p=BEFORE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old)
            files[name]={'before_sha256':hashlib.sha256(old).hexdigest()}
        else:files[name]={'before_sha256':None}
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    files[name]['sha256']=hashlib.sha256(data).hexdigest()
    index.write_text(json.dumps(files,indent=2)+'\n')

# Label, official artwork app, retained working source resource root, old names.
APPS=[
('AudioFX','AudioFX','packages/apps/AudioFX/res',['mipmap/ic_launcher']),
('Browser','Jelly','packages/apps/Jelly/app/src/main/res',['mipmap/ic_launcher']),
('Calculator','ExactCalculator','packages/apps/ExactCalculator/res',['mipmap/ic_launcher_calculator']),
('Calendar','Etar','packages/apps/Calendar/res',['mipmap/ic_launcher_calendar']),
('Camera','Aperture','packages/apps/Camera2/res',['mipmap/logo_camera_color_44in48dp']),
('Clock','DeskClock','packages/apps/DeskClock/res',['mipmap/ic_launcher_alarmclock']),
('Contacts','Contacts','packages/apps/Contacts/res',['mipmap/ic_contacts_launcher','mipmap/ic_contacts_round']),
('Email','Email','packages/apps/Email/res',['mipmap/ic_launcher_mail']),
('Files','DocumentsUI','frameworks/base/packages/DocumentsUI/res',['mipmap/ic_launcher_filemanager','drawable/app_icon']),
('Gallery','Glimpse','packages/apps/Gallery2/res',['mipmap/ic_launcher_gallery']),
('Music','Eleven','packages/apps/Eleven/res',['mipmap/ic_launcher_eleven']),
('Recorder','Recorder','packages/apps/Recorder/app/src/main/res',['mipmap/ic_launcher']),
('Settings','Settings','packages/apps/Settings/res',['mipmap/ic_launcher_settings']),
]
densities={'mdpi':48,'hdpi':72,'xhdpi':96,'xxhdpi':144,'xxxhdpi':192}
records=[]
# Remove a superseded mapping only after checking every owned file. The active
# ROM uses AOSP Camera2, not the unused Snap project.
previous_manifest=ROOT/'port-manifest.json'
if previous_manifest.is_file():
    desired={label:destination for label,app,destination,aliases in APPS}
    for record in json.loads(previous_manifest.read_text())['apps']:
        if record['retained_source_root']==desired[record['label']]:continue
        for name in record['generated']:
            if name not in files:continue
            entry=files[name];target=SRC/name
            assert target.resolve().is_relative_to(SRC.resolve())
            assert hashlib.sha256(target.read_bytes()).hexdigest()==entry['sha256'],name
            if entry['before_sha256'] is None:target.unlink()
            else:
                original=(BEFORE/name).read_bytes()
                assert hashlib.sha256(original).hexdigest()==entry['before_sha256']
                target.write_bytes(original)
            del files[name]
    index.write_text(json.dumps(files,indent=2)+'\n')
for label,app,destination,aliases in APPS:
    repo='android_packages_apps_'+app
    svg=ET.Element('{'+S+'}svg',{'width':'192','height':'192','viewBox':'18 18 72 72'})
    defs=node(svg,'defs');clip=node(defs,'clipPath',{'id':'icon-mask'})
    node(clip,'circle',{'cx':'54','cy':'54','r':'36'})
    content=node(svg,'g',{'clip-path':'url(#icon-mask)'})
    if app=='Email':
        for name in ('ic_background.png','ic_foreground.png'):
            p=UP/repo/'res/mipmap-xxxhdpi'/name
            assert p.is_file(),p
            im=node(content,'image',{'x':'0','y':'0','width':'108','height':'108'})
            im.set('{http://www.w3.org/1999/xlink}href','data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode())
    else:
        layer(repo,'ic_launcher_background.xml',content,defs)
        layer(repo,'ic_launcher_foreground.xml',content,defs)
    data=ET.tostring(svg,encoding='utf-8',xml_declaration=True)
    (RENDER/(label+'.svg')).write_bytes(data)
    generated=[]
    for density,size in densities.items():
        png=cairosvg.svg2png(bytestring=data,output_width=size,output_height=size)
        with Image.open(io.BytesIO(png)) as image:
            assert image.size==(size,size)
            assert image.mode=='RGBA'
            assert image.getpixel((0,0))[3]==0,'Mask corner is not transparent'
            assert image.getbbox() and image.getbbox()[2]>=size-1,'Unexpectedly empty icon'
        name=destination+'/mipmap-'+density+'/t110_modern_launcher.png'
        binary(name,png);generated.append(name)
        if size==192:(RENDER/(label+'.png')).write_bytes(png)
    # AAPT1 does not compile XML stored under mipmap. Remove only our earlier
    # generated aliases (never an original project resource), then use ordinary
    # PNG resource IDs directly from each original application manifest.
    for old in aliases:
        kind,name=old.split('/')
        stale=destination+'/'+kind+'-anydpi-v25/'+name+'.xml'
        if stale in files:
            assert files[stale]['before_sha256'] is None,stale
            target=SRC/stale
            assert target.resolve().is_relative_to(SRC.resolve())
            assert hashlib.sha256(target.read_bytes()).hexdigest()==files[stale]['sha256']
            target.unlink()
            del files[stale]
    index.write_text(json.dumps(files,indent=2)+'\n')
    manifest_name=str(Path(destination).parent/'AndroidManifest.xml')
    original=read(manifest_name)
    updated=original
    for old in aliases:
        updated=re.sub(r'(android:(?:icon|roundIcon)\s*=\s*")@'+re.escape(old)+r'(")',
                       r'\1@mipmap/t110_modern_launcher\2',updated)
    assert '@mipmap/t110_modern_launcher' in updated,manifest_name
    save(manifest_name,updated)
    generated.append(manifest_name)
    records.append({'label':label,'upstream_artwork':'LineageOS/'+repo,
        'retained_source_root':destination,'original_icon_resources':aliases,
        'manifest':manifest_name,'generated':generated})
sheet=Image.new('RGB',(1000,720),'#e8ece9');draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
for i,r in enumerate(records):
    x=(i%5)*200;y=(i//5)*240
    icon=Image.open(RENDER/(r['label']+'.png'))
    sheet.paste(icon,(x+4,y+8),icon)
    draw.text((x+100,y+210),r['label'],font=font,fill='#19211c',anchor='mm')
sheet.save(RENDER/'contact-sheet.png')
(ROOT/'port-manifest.json').write_text(json.dumps({
    'scope':'13 native app icon-resource backports only; all existing apps/code/APIs retained',
    'api':25,'shape':'circle','adaptive_crop_viewbox':'18 18 72 72',
    'renderer':'CairoSVG '+cairosvg.__version__,'apps':records},indent=2)+'\n')
print('Ported',len(records),'official app icons in five densities; native manifests select PNG resources.')
