"""Retain legacy GPU allocation ownership across asynchronous capture delivery."""
from pathlib import Path
import subprocess,difflib,hashlib,json
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');t=Path('/root/t110-build/lineage20')
f=t/'frameworks/native/libs/gui/ScreenCaptureResults.cpp';before=f.read_text()
assert 'T110CaptureBufferOwner' not in before
after=before.replace('#include <gui/ScreenCaptureResults.h>','#include <gui/ScreenCaptureResults.h>\n#include <android-base/properties.h>\n#include <binder/Binder.h>')
after=after.replace('namespace android::gui {','''namespace android::gui {
namespace {
constexpr int32_t kT110CaptureOwnerTag = 0x5431314f;

// This driver transports memory FDs, but its allocation owner also holds GPU
// signals needed while registerBuffer imports the handle in another process.
// Binder retains this object during delivery; the imported GraphicBuffer then
// retains the token until its own cleanup. No delayed release or global cache.
class T110CaptureBufferOwner final : public BBinder {
public:
    explicit T110CaptureBufferOwner(const sp<GraphicBuffer>& buffer) : mBuffer(buffer) {}
private:
    const sp<GraphicBuffer> mBuffer;
};

bool retainT110CaptureOwner() {
    static const bool enabled = base::GetBoolProperty("ro.t110.legacy_gpu", false);
    return enabled;
}
} // namespace
''',1)
anchor='    SAFE_PARCEL(parcel->writeInt32, result);\n    return NO_ERROR;'
assert anchor in after
after=after.replace(anchor,'''    SAFE_PARCEL(parcel->writeInt32, result);
    if (retainT110CaptureOwner() && buffer != nullptr) {
        SAFE_PARCEL(parcel->writeInt32, kT110CaptureOwnerTag);
        SAFE_PARCEL(parcel->writeStrongBinder, sp<T110CaptureBufferOwner>::make(buffer));
    }
    return NO_ERROR;''',1)
anchor='    SAFE_PARCEL(parcel->readInt32, &result);\n    return NO_ERROR;'
assert anchor in after
after=after.replace(anchor,'''    SAFE_PARCEL(parcel->readInt32, &result);
    if (retainT110CaptureOwner() && buffer != nullptr && parcel->dataAvail() >= sizeof(int32_t)) {
        // Older capture payloads do not have this device-only extension.
        const size_t position = parcel->dataPosition();
        int32_t tag = 0;
        SAFE_PARCEL(parcel->readInt32, &tag);
        if (tag == kT110CaptureOwnerTag) {
            sp<IBinder> owner;
            SAFE_PARCEL(parcel->readStrongBinder, &owner);
            if (owner == nullptr) return BAD_VALUE;
            // GraphicBuffer invokes these callbacks after freeing its handle.
            buffer->addDeathCallback([owner](void*, uint64_t) { (void)owner; }, nullptr);
        } else {
            parcel->setDataPosition(position);
        }
    }
    return NO_ERROR;''',1)
f.write_text(after)
patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/libs/gui/ScreenCaptureResults.cpp',tofile='b/libs/gui/ScreenCaptureResults.cpp'))
(p/'patches/0080-gui-t110-retain-capture-buffer-owner.patch').write_text(patch)
(p/'work/device/samsung/t110_bringup/graphics/CaptureResultsCompat.cpp').write_text(after)
e=p/'evidence/offline-v41';(e/'capture-owner-source.json').write_text(json.dumps({'before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':hashlib.sha256(after.encode()).hexdigest(),'cpp_only':True,'public_struct_layout_changed':False,'callback_oneway_semantics_changed':False,'other_devices_wire_format_changed':False},indent=2)+'\n')
print('CAPTURE_OWNER_FIX_SOURCE_PREPARED')
