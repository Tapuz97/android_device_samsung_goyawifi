/* SPDX-License-Identifier: Apache-2.0 */
#pragma once

#include <android-base/parseint.h>
#include <sysutils/NetlinkEvent.h>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <optional>

namespace android::net {
struct IdletimerActivity {
    int label;
    bool active;
    int64_t timestamp;
    int uid;
};

inline std::optional<IdletimerActivity> parseIdletimerActivity(NetlinkEvent& event) {
    const char* label = event.findParam("INTERFACE");
    // Older IDLETIMER kernels name this field LABEL. Both contain the same
    // interface-class identifier; missing labels must never reach ParseInt.
    if (label == nullptr) label = event.findParam("LABEL");
    const char* state = event.findParam("STATE");
    int intLabel;
    if (label == nullptr || state == nullptr || !android::base::ParseInt(label, &intLabel)) {
        return std::nullopt;
    }
    const bool active = !strcmp(state, "active");
    const char* timestamp = event.findParam("TIME_NS");
    const char* uid = event.findParam("UID");
    return IdletimerActivity{intLabel, active,
                            timestamp == nullptr ? 0 : strtoll(timestamp, nullptr, 10),
                            uid != nullptr && active ? static_cast<int>(strtol(uid, nullptr, 10)) : -1};
}
}  // namespace android::net
