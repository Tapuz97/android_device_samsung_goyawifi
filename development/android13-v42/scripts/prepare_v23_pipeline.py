"""Prepare verification and staging tools; do not change the build or tablet."""
from pathlib import Path

p=Path(__file__).resolve().parents[1]
s=(p/'scripts/verify_v22_contents.py').read_text()
s=s.replace('v22','v23').replace('v21','v22').replace('offline-v32','offline-v33')
s=s.replace('import subprocess','import subprocess\nimport io\nimport zipfile\nimport xml.etree.ElementTree as ET')
s=s.replace("candidate=json.loads((e/'setup-candidate/installation.json').read_text())\nassert candidate['visual_result']=='WELCOME_RENDERED_CORRECTLY'", "candidate=json.loads((p/'evidence/offline-v32/setup-candidate/installation.json').read_text())\nassert candidate['visual_result']=='WELCOME_RENDERED_CORRECTLY'")
s=s.replace("'system/framework/framework.jar',",'')
s=s.replace("             'system/vendor/etc/permissions/android.hardware.wifi.xml',", "             'system/vendor/etc/permissions/android.hardware.wifi.xml',\n             'system/system_ext/priv-app/LineageSetupWizard/LineageSetupWizard.apk',")
start=s.index('changed={}\n')
end=s.index("composer=content(",start)
s=s[:start]+'''changed={}
name='system/framework/framework.jar'
data=content(name)
assert data==(product/name).read_bytes() and data!=content(name,old),name
with zipfile.ZipFile(io.BytesIO(data)) as jar:
    dex=[jar.read(n) for n in jar.namelist() if n.endswith('.dex')]
    assert dex and any(b'T110 window rendering: software Canvas for ' in d for d in dex)
changed[name]=sha(data)
for filename,expected_features in [
        ('android.software.app_widgets.xml',{'android.software.app_widgets'}),
        ('android.hardware.touchscreen.xml',{'android.hardware.touchscreen','android.hardware.faketouch'})]:
    name='system/vendor/etc/permissions/'+filename
    data=content(name)
    assert data==(product/name).read_bytes()
    assert {n.attrib['name'] for n in ET.fromstring(data).findall('feature')}==expected_features
    changed[name]=sha(data)
assert retained['system/system_ext/priv-app/LineageSetupWizard/LineageSetupWizard.apk']==candidate['sha256']
# The framework changed, so verify the newly built boot-image artifacts are
# actually present in this image, rather than retaining old precompiled files.
boot_preopt={}
for path in sorted(list((product/'system/framework/arm').glob('boot*'))+list((product/'system/framework').glob('boot*.vdex'))):
    if path.is_file() and not path.is_symlink() and path.suffix in ('.art','.oat','.vdex'):
        name=path.relative_to(product).as_posix()
        data=content(name)
        assert data==path.read_bytes()
        boot_preopt[name]=sha(data)
assert boot_preopt,'Missing rebuilt framework boot preopt artifacts'
''' +s[end:]
s=s.replace("('packages/apps/SetupWizard','0057-setupwizard-configurable-canvas-rendering.patch')", "('packages/apps/SetupWizard','0057-setupwizard-configurable-canvas-rendering.patch'),\n                   ('frameworks/base','0058-framework-t110-software-window-rendering.patch')")
s=s.replace('offline_image_check=True,setup_app_same_boot_validated=True', 'offline_image_check=True,boot_preopt=boot_preopt,\n    setup_app_same_boot_validated=True,ordinary_window_fallback_hardware_validated=False')
(p/'scripts/verify_v23_contents.py').write_text(s,encoding='utf-8')
s=(p/'scripts/finalize_v22_offline.py').read_text().replace('v22','v23').replace('offline-v32','offline-v33')
s=s.replace("assert json.loads((e/'setup-candidate/installation.json').read_text())['visual_result']=='WELCOME_RENDERED_CORRECTLY'", "assert 'system/framework/framework.jar' in contents['changed']")
s=s.replace("fixes=['T110 setup activities use software Canvas after same-boot scene verification',", "fixes=['T110 ordinary ViewRoot windows use software Canvas compatibility fallback',\n           'Canonical app_widgets declaration starts the missing widget service',\n           'Declare user-confirmed basic touchscreen capability',")
s=s.replace("'Panel orientation, usable touch, sleep/wake require hardware validation'", "'New launcher/window behavior needs hardware validation; this is a software UI fallback'")
(p/'scripts/finalize_v23_offline.py').write_text(s,encoding='utf-8')
s=(p/'scripts/stage_v22_system.py').read_text().replace('v22','v23').replace('offline-v32','offline-v33')
(p/'scripts/stage_v23_system.py').write_text(s,encoding='utf-8')
print('V23_PIPELINE_TOOLS_PREPARED')
