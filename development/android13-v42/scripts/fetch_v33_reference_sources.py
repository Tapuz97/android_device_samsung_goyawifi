"""Save upstream references locally while the build disk is unavailable.

These are investigation copies only; patches must be checked against the pinned tree.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import urllib.request

root = Path(__file__).resolve().parents[1]
out = root / 'evidence/offline-v33/upstream-reference'
out.mkdir(parents=True, exist_ok=True)
files = {
    'android_frameworks_base': [
        'libs/hwui/renderthread/EglManager.cpp',
        'core/java/android/view/ViewRootImpl.java',
        'core/java/android/view/ThreadedRenderer.java',
        'graphics/java/android/graphics/HardwareRenderer.java',
        'services/java/com/android/server/SystemServer.java',
    ],
    'android_frameworks_native': ['opengl/libs/EGL/eglApi.cpp'],
    'android_packages_apps_Trebuchet': [
        'src/com/android/launcher3/widget/WidgetManagerHelper.java',
        'AndroidManifest.xml',
    ],
}

def fetch(item):
    repo, name = item
    url = f'https://raw.githubusercontent.com/LineageOS/{repo}/lineage-20.0/{name}'
    data = urllib.request.urlopen(url, timeout=30).read()
    target = out/repo/name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return dict(url=url, file=str(target.relative_to(out)), sha256=hashlib.sha256(data).hexdigest())

with ThreadPoolExecutor(max_workers=4) as pool:
    report = list(pool.map(fetch, [(r,n) for r,names in files.items() for n in names]))
(out/'provenance.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print('Saved', len(report), 'upstream reference files; not build inputs.')
