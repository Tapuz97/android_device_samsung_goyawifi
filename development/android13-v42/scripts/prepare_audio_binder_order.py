"""Configure Binder pool size before either C++ or NDK starts the pool."""
from pathlib import Path
import subprocess

project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
repo = Path('/root/t110-build/lineage20/hardware/interfaces')
relative = 'audio/common/all-versions/default/service/service.cpp'
path = repo / relative
old = '''    // start a threadpool for vndbinder interactions
    ::android::ProcessState::self()->startThreadPool();

    ABinderProcess_setThreadPoolMaxThreadCount(1);
    ABinderProcess_startThreadPool();'''
new = '''    // Configure first: on legacy non-VNDK products, C++ and NDK Binder
    // share one ProcessState. Resizing it after startThreadPool would abort.
    ABinderProcess_setThreadPoolMaxThreadCount(1);
    // start a threadpool for vndbinder interactions
    ::android::ProcessState::self()->startThreadPool();
    ABinderProcess_startThreadPool();'''
source = path.read_text()
assert source.count(old) == 1
path.write_text(source.replace(old, new))
patch = subprocess.check_output(['git', '-C', str(repo), 'diff', '--', relative])
assert b'ABinderProcess_setThreadPoolMaxThreadCount' in patch
(project / 'patches/0029-audio-binder-pool-initialization-order.patch').write_bytes(patch)
print('Audio Binder pool initialization reordered; scoped patch exported.')
