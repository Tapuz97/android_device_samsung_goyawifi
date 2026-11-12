/*
 * Copyright 2021 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <gui/ScreenCaptureResults.h>
#include <android-base/properties.h>
#include <binder/Binder.h>

#include <private/gui/ParcelUtils.h>

namespace android::gui {
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


status_t ScreenCaptureResults::writeToParcel(android::Parcel* parcel) const {
    if (buffer != nullptr) {
        SAFE_PARCEL(parcel->writeBool, true);
        SAFE_PARCEL(parcel->write, *buffer);
    } else {
        SAFE_PARCEL(parcel->writeBool, false);
    }

    if (fence != Fence::NO_FENCE) {
        SAFE_PARCEL(parcel->writeBool, true);
        SAFE_PARCEL(parcel->write, *fence);
    } else {
        SAFE_PARCEL(parcel->writeBool, false);
    }

    SAFE_PARCEL(parcel->writeBool, capturedSecureLayers);
    SAFE_PARCEL(parcel->writeBool, capturedHdrLayers);
    SAFE_PARCEL(parcel->writeUint32, static_cast<uint32_t>(capturedDataspace));
    SAFE_PARCEL(parcel->writeInt32, result);
    if (retainT110CaptureOwner() && buffer != nullptr) {
        SAFE_PARCEL(parcel->writeInt32, kT110CaptureOwnerTag);
        SAFE_PARCEL(parcel->writeStrongBinder, sp<T110CaptureBufferOwner>::make(buffer));
    }
    return NO_ERROR;
}

status_t ScreenCaptureResults::readFromParcel(const android::Parcel* parcel) {
    bool hasGraphicBuffer;
    SAFE_PARCEL(parcel->readBool, &hasGraphicBuffer);
    if (hasGraphicBuffer) {
        buffer = new GraphicBuffer();
        SAFE_PARCEL(parcel->read, *buffer);
    }

    bool hasFence;
    SAFE_PARCEL(parcel->readBool, &hasFence);
    if (hasFence) {
        fence = new Fence();
        SAFE_PARCEL(parcel->read, *fence);
    }

    SAFE_PARCEL(parcel->readBool, &capturedSecureLayers);
    SAFE_PARCEL(parcel->readBool, &capturedHdrLayers);
    uint32_t dataspace = 0;
    SAFE_PARCEL(parcel->readUint32, &dataspace);
    capturedDataspace = static_cast<ui::Dataspace>(dataspace);
    SAFE_PARCEL(parcel->readInt32, &result);
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
    return NO_ERROR;
}

} // namespace android::gui
