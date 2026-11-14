"""Restore only this target's exact pinned ARM LFS object; validate every byte."""
from pathlib import Path
import hashlib
import json
import configparser
import shutil
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

audit = Path('/root/t110-android13-audit')
android = Path('/root/t110-android13/android')
relative = 'external/chromium-webview/prebuilt/arm'
project = ET.parse(audit/'restored/source-delta/pinned-manifest.xml').find(f".//project[@path='{relative}']")
assert project is not None
revision = project.attrib['revision']
assert revision == '472d0ac3cf8e78982807bedd20279a537d6cdf68'
expected = '0dc261c3f37e9ac16a4f593ef316a097fc59815bb2082a8e38c519647bbcb3cc'
expected_size = 98126751
target = android/relative/'webview.apk'
config = configparser.ConfigParser()
config.read(android/relative/'.lfsconfig')
url = config['lfs']['url'].strip('"')
assert url == 'https://review.lineageos.org/LineageOS/android_external_chromium-webview_prebuilt_arm.git/info/lfs'
def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else digest(f)
def digest(f):
    h = hashlib.sha256()
    for data in iter(lambda: f.read(1024*1024), b''): h.update(data)
    return h.hexdigest()
if target.stat().st_size != expected_size or sha(target) != expected:
    pointer = target.read_text()
    assert f'oid sha256:{expected}' in pointer and f'size {expected_size}' in pointer
    temporary = target.with_suffix('.apk.downloading')
    request = urllib.request.Request(url+'/objects/batch', data=json.dumps(dict(
        operation='download', transfers=['basic'], objects=[dict(oid=expected,size=expected_size)])).encode(),
        headers={'Content-Type':'application/vnd.git-lfs+json','Accept':'application/vnd.git-lfs+json'})
    with urllib.request.urlopen(request, timeout=90) as response:
        batch = json.load(response)
    obj = batch['objects'][0]
    assert obj['oid'] == expected and obj['size'] == expected_size and 'error' not in obj, obj
    download = obj['actions']['download']
    request = urllib.request.Request(download['href'], headers=download.get('header',{}))
    with urllib.request.urlopen(request, timeout=90) as response, temporary.open('wb') as output:
        shutil.copyfileobj(response, output, 1024*1024)
    assert temporary.stat().st_size == expected_size and sha(temporary) == expected
    with zipfile.ZipFile(temporary) as archive:
        assert archive.testzip() is None
        assert 'AndroidManifest.xml' in archive.namelist()
        assert 'lib/armeabi-v7a/libwebviewchromium.so' in archive.namelist()
    temporary.replace(target)
result = dict(status='PASS', project=project.attrib['name'], revision=revision,
              path=relative+'/webview.apk', url=url, bytes=expected_size, sha256=expected,
              source_revision_changed=False, flashed=False)
(audit/'pinned-webview-verification.json').write_text(json.dumps(result, indent=2)+'\n')
print('PASS exact pinned ARM WebView LFS payload restored and ZIP/hash checked.')
