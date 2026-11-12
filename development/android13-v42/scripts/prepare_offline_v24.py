"""Apply source fixes on the build machine only; never connects to a tablet."""
from pathlib import Path
import subprocess

project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
tree = Path('/root/t110-build/lineage20')

def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)

gnss = tree / 'frameworks/base/services/core/jni/gnss/Gnss.cpp'
s = gnss.read_text()
assert 'T110 GNSS' not in s, 'Already applied; inspect instead of duplicating'
s = replace_once(s, '#include <binder/IServiceManager.h>',
    '#include <binder/IServiceManager.h>\n#include <android-base/properties.h>\n'
    '#include <android/hidl/manager/1.0/IServiceManager.h>\n'
    '#include <hidl/ServiceManagement.h>')
helper = '''// A legacy product without VINTF enforcement otherwise sleeps for every absent
// HIDL version and tries to launch it. Do not wait on the system-server main
// thread for providers this product has not declared or made ready.
template <typename Interface>
sp<Interface> getGnssHidlService(bool declaredOnly) {
    if (!declaredOnly) return Interface::getService();
    auto manager = hardware::defaultServiceManager();
    if (manager == nullptr) return nullptr;
    auto transport = manager->getTransport(Interface::descriptor, "default");
    using Transport = hardware::hidl::manager::V1_0::IServiceManager::Transport;
    if (!transport.isOk() || transport == Transport::EMPTY) return nullptr;
    return Interface::tryGetService();
}

'''
# IServiceManager lives in android::hidl, not android::hardware::hidl.
helper = helper.replace('hardware::hidl::manager', 'hidl::manager')
s = replace_once(s, 'namespace {\n', 'namespace {\n\n' + helper)
s = replace_once(s, '    gnssHalAidl = waitForVintfService<IGnssAidl>();',
    '    const bool declaredOnly = base::GetBoolProperty("ro.t110.optional_hal_probe", false);\n'
    '    if (declaredOnly) ALOGI("T110 GNSS probing declared services without waiting");\n'
    '    gnssHalAidl = declaredOnly ? checkVintfService<IGnssAidl>()\n'
    '                               : waitForVintfService<IGnssAidl>();')
for interface in ['IGnss_V2_1', 'IGnss_V2_0', 'IGnss_V1_1', 'IGnss_V1_0']:
    s = replace_once(s, f'= {interface}::getService();',
                     f'= getGnssHidlService<{interface}>(declaredOnly);')
gnss.write_text(s)
bp = tree / 'frameworks/base/services/core/jni/gnss/Android.bp'
s = replace_once(bp.read_text(), '    name: "libservices.core-gnss",',
                 '    name: "libservices.core-gnss",\n    shared_libs: ["libbase"],')
bp.write_text(s)

lmkd = tree / 'system/memory/lmkd/lmkd.cpp'
s = lmkd.read_text()
old = '    ALOGI("lmkd data connection established");'
new = '''    // Linux 3.4 does not inherit the listener's SOCK_PASSCRED flag in
    // unix_accept(). Set it on each accepted socket before reading packets.
    // Keep SCM_CREDENTIALS mandatory; never substitute unverified peer data.
    int passcred = 1;
    if (setsockopt(data_sock[free_dscock_idx].sock, SOL_SOCKET, SO_PASSCRED,
                   &passcred, sizeof(passcred)) < 0) {
        ALOGE("lmkd accepted socket SO_PASSCRED failed: %s", strerror(errno));
        close(data_sock[free_dscock_idx].sock);
        data_sock[free_dscock_idx].sock = -1;
        return;
    }

''' + old
s = replace_once(s, old, new)
lmkd.write_text(s)

for repo, patch in [('frameworks/base','0040-gnss-t110-declared-service-probe.patch'),
                    ('system/memory/lmkd','0041-lmkd-accepted-socket-credentials.patch')]:
    diff = subprocess.check_output(['git','-C',str(tree/repo),'diff','--binary'])
    assert diff
    (project/'patches'/patch).write_bytes(diff)
    subprocess.run(['git','-C',str(tree/repo),'diff','--check'],check=True)
print('V24 source changes prepared offline')
