"""Prepare the three captured startup corrections without accessing the tablet."""
from pathlib import Path
import difflib
import json
import subprocess

p = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
tree = Path('/root/t110-build/lineage20')
evidence = p/'evidence/offline-v27'
evidence.mkdir(exist_ok=True)

def patch(repository, path, name, before, after):
    target = tree/repository/path
    text = target.read_text()
    if after in text:
        subprocess.run(['git','apply','--reverse','--check',str(p/'patches'/name)],cwd=tree/repository,check=True)
        return
    assert text.count(before) == 1, (path, text.count(before))
    updated = text.replace(before, after)
    delta = ''.join(difflib.unified_diff(text.splitlines(True),updated.splitlines(True),
        fromfile='a/'+path,tofile='b/'+path))
    (evidence/(target.name+'.before')).write_text(text)
    (p/'patches'/name).write_text(delta)
    subprocess.run(['git','apply','--check',str(p/'patches'/name)],cwd=tree/repository,check=True)
    target.write_text(updated)
    subprocess.run(['git','apply','--reverse','--check',str(p/'patches'/name)],cwd=tree/repository,check=True)
    (evidence/target.name).write_text(updated)

patch('packages/modules/Connectivity','service-t/src/com/android/server/net/NetworkStatsService.java',
      '0049-networkstats-global-alert-service-errors.patch',
'''            mNetd.bandwidthSetGlobalAlert(mGlobalAlertBytes);
        } catch (IllegalStateException e) {
            Log.w(TAG, "problem registering for global alert: " + e);
''',
'''            mNetd.bandwidthSetGlobalAlert(mGlobalAlertBytes);
        } catch (IllegalStateException | ServiceSpecificException e) {
            // Kernel quota support can be unavailable. Keep scheduled polling
            // and provider alerts active; a rejected netd alert is not a
            // reason to terminate system_server from the polling receiver.
            Log.w(TAG, "Global bandwidth alert unavailable; retaining polling: " + e);
''')

patch('system/netd','server/BandwidthController.cpp',
      '0050-netd-global-alert-commit-on-success.patch',
'''    mGlobalAlertBytes = bytes;
    return res;
}

int BandwidthController::removeGlobalAlert()''',
'''    // A failed iptables insertion did not create the quota node. Preserve
    // the prior state so the next registration retries insertion, rather
    // than trying to update a nonexistent /proc/net/xt_quota/globalAlert.
    if (res == 0) mGlobalAlertBytes = bytes;
    return res;
}

int BandwidthController::removeGlobalAlert()''')

patch('external/libfuse','include/fuse_kernel.h',
      '0051-libfuse-unsigned-passthrough-mask.patch',
      '#define FUSE_PASSTHROUGH\t(1 << 31)',
      '#define FUSE_PASSTHROUGH\t(1U << 31)')
common=tree/'external/libfuse/include/fuse_common.h'
text=common.read_text()
old='#define FUSE_CAP_PASSTHROUGH            (1 << 31)'
new='#define FUSE_CAP_PASSTHROUGH            (1U << 31)'
if new not in text:
    assert text.count(old)==1
    (evidence/'fuse_common.h.before').write_text(text)
    common.write_text(text.replace(old,new))
# Keep the protocol and public capability mask correction in one patch.
(p/'patches/0051-libfuse-unsigned-passthrough-mask.patch').write_bytes(
    subprocess.check_output(['git','diff','--','include/fuse_kernel.h','include/fuse_common.h'],
                            cwd=tree/'external/libfuse'))
(evidence/'fuse_common.h').write_bytes(common.read_bytes())

mk = p/'work/device/samsung/t110_bringup/t110_system.mk'
text = mk.read_text()
addition = '''
# This Wi-Fi tablet needs its feature declaration for SystemServer to start
# the existing WifiService. Radio/HAL functionality still requires porting.
PRODUCT_COPY_FILES += \\
    frameworks/native/data/etc/android.hardware.wifi.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.wifi.xml

# Samsung's Jelly Bean sdcardfs rejects the modern fsuid/fsgid/mask options.
# Select Android's existing MediaProvider FUSE path. Keep its access checks;
# do not require newer ext4 casefold/project-quota features on existing data.
PRODUCT_SYSTEM_PROPERTIES += external_storage.sdcardfs.enabled=false
'''
if addition not in text:
    (evidence/'t110_system.mk.before').write_text(text)
    mk.write_text(text.rstrip()+'\n'+addition)
(evidence/'t110_system.mk').write_bytes(mk.read_bytes())

script = p/'scripts/build_system_image.sh'
text = script.read_text()
old = " 'frameworks/native:0047-egl-t110-process-initialization.patch'; do"
new = " 'frameworks/native:0047-egl-t110-process-initialization.patch' 'packages/modules/Connectivity:0049-networkstats-global-alert-service-errors.patch' 'system/netd:0050-netd-global-alert-commit-on-success.patch'; do"
if 'packages/modules/Connectivity:0049-networkstats-global-alert-service-errors.patch' not in text:
    assert old in text
    script.write_text(text.replace(old,new))
text = script.read_text()
if 'external/libfuse:0051-libfuse-unsigned-passthrough-mask.patch' not in text:
    assert new in text
    script.write_text(text.replace(new,new.replace('; do'," 'external/libfuse:0051-libfuse-unsigned-passthrough-mask.patch'; do")))

report = dict(status='SOURCES_READY_FOR_OFFLINE_CHECKS', tablet_access=False,android_boots=0,
    changes=['Wi-Fi feature declaration starts existing framework service',
             'NetworkStats handles rejected global alerts while retaining polling/provider callbacks',
             'netd caches global-alert installation only after successful kernel operation',
             'Use an unsigned FUSE bit31 mask to eliminate signed-shift undefined behavior',
             'Use existing MediaProvider FUSE path instead of incompatible Samsung sdcardfs'],
    limits=['Radio functionality is not established by declaring its actual hardware feature',
            'FUSE protocol and mount path require offline audit and eventual hardware verification'])
(evidence/'sources.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
