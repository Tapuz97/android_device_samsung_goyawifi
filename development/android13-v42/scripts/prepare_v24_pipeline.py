"""Prepare gates that require the exact launcher proven on the existing boot."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
s=(p/'scripts/verify_v23_contents.py').read_text().replace('v23','v24').replace('v22','v23').replace('offline-v33','offline-v34')
s=s.replace("candidate=json.loads((p/'evidence/offline-v32/setup-candidate/installation.json').read_text())\nassert candidate['visual_result']=='WELCOME_RENDERED_CORRECTLY'", "candidate=json.loads((e/'launcher-candidate/installation.json').read_text())\nassert candidate['visual_result']=='HOME_DRAWER_SETTINGS_RECENTS_RENDER_CORRECTLY'")
s=s.replace(",'system/system_ext/priv-app/SystemUI/SystemUI.apk'",'')
s=s.replace("             'system/system_ext/priv-app/LineageSetupWizard/LineageSetupWizard.apk',\n",'')
s=s.replace("data==(product/name).read_bytes() and data!=content(name,old),name", "data==(product/name).read_bytes()==content(name,old),name")
s=s.replace("changed[name]=sha(data)\nfor filename,expected_features", "retained[name]=sha(data)\nfor filename,expected_features")
needle="assert retained['system/system_ext/priv-app/LineageSetupWizard/LineageSetupWizard.apk']==candidate['sha256']"
assert needle in s
s=s.replace(needle,'''for app in ['TrebuchetQuickStep','SystemUI','LineageSetupWizard','Settings']:
    name=f'system/system_ext/priv-app/{app}/{app}.apk'
    data=content(name)
    assert data==(product/name).read_bytes(),name
    if app=='TrebuchetQuickStep':
        assert sha(data)==candidate['sha256']
        assert data==(e/'launcher-candidate/TrebuchetQuickStep.apk').read_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as jar:
        dex=b''.join(jar.read(n) for n in jar.namelist() if n.endswith('.dex'))
    if app in ('TrebuchetQuickStep','SystemUI'):
        assert b't110_bringup' in dex,app
    if data==content(name,old): retained[name]=sha(data)
    else: changed[name]=sha(data)
''')
s=s.replace("('frameworks/base','0058-framework-t110-software-window-rendering.patch')", "('frameworks/base','0058-framework-t110-software-window-rendering.patch'),\n                   ('frameworks/libs/systemui','0059-iconloader-t110-software-bitmaps.patch'),\n                   ('frameworks/base','0060-systemui-shared-t110-software-task-snapshots.patch')")
s=s.replace('ordinary_window_fallback_hardware_validated=False','ordinary_window_fallback_hardware_validated=True,\n    launcher_candidate_same_boot_validated=True,full_image_hardware_validated=False')
(p/'scripts/verify_v24_contents.py').write_text(s,encoding='utf-8')
s=(p/'scripts/finalize_v23_offline.py').read_text().replace('v23','v24').replace('offline-v33','offline-v34')
s=s.replace("assert 'system/framework/framework.jar' in contents['changed']", "assert contents['launcher_candidate_same_boot_validated']\nassert 'system/framework/framework.jar' in contents['retained']")
s=s.replace("fixes=['T110 ordinary", "fixes=['Generated and cached launcher icons use CPU-readable bitmaps',\n           'Recents converts owned hardware snapshots before software drawing',\n           'T110 ordinary")
(p/'scripts/finalize_v24_offline.py').write_text(s,encoding='utf-8')
s=(p/'scripts/stage_v23_system.py').read_text().replace('v23','v24').replace('offline-v33','offline-v34')
(p/'scripts/stage_v24_system.py').write_text(s,encoding='utf-8')
s=(p/'scripts/prepare_v23_recovery.py').read_text().replace('v23','v24').replace('V23','V24').replace('offline-v33','offline-v34')
needle='    try:run(helper,check=False)'
assert needle in s
s=s.replace(needle,'''    # Test the ROM's embedded APK next, not the temporary successful app update.
    receipt=run('pm uninstall-system-updates com.android.launcher3',timeout=120,check=False)
    assert 'Success' in receipt,receipt
    path=run('pm path com.android.launcher3').strip()
    assert path=='package:/system/system_ext/priv-app/TrebuchetQuickStep/TrebuchetQuickStep.apk',path
    (p/'evidence/offline-v34/launcher-candidate/update-removed-before-rom.json').write_text(
        json.dumps(dict(receipt=receipt,path=path),indent=2)+'\\n')
    try:run(helper,check=False)''')
(p/'scripts/prepare_v24_recovery.py').write_text(s,encoding='utf-8')
s=(p/'scripts/install_verified_v23.py').read_text().replace('v23','v24')
(p/'scripts/install_verified_v24.py').write_text(s,encoding='utf-8')
s=(p/'scripts/finish_v23_build_and_install.py').read_text().replace('v23','v24').replace('20261107T144041Z','20261107T153115Z')
(p/'scripts/finish_v24_build_and_install.py').write_text(s,encoding='utf-8')
print('V24_VERIFICATION_INSTALL_PIPELINE_PREPARED')
