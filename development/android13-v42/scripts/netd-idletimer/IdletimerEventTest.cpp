/* SPDX-License-Identifier: Apache-2.0 */
#include "IdletimerEvent.h"
#include <gtest/gtest.h>
#include <sysutils/NetlinkListener.h>
#include <initializer_list>
#include <string>

namespace android::net {
static std::optional<IdletimerActivity> decode(std::initializer_list<const char*> attributes) {
    // Replay the real NUL-separated kernel UEVENT format, not a fake event API.
    std::string wire("change@/devices/virtual/xt_idletimer/xt_idletimer");
    wire.push_back('\0');
    for (const char* attribute : attributes) {
        wire.append(attribute);
        wire.push_back('\0');
    }
    NetlinkEvent event;
    EXPECT_TRUE(event.decode(wire.data(), wire.size(), NetlinkListener::NETLINK_FORMAT_ASCII));
    return parseIdletimerActivity(event);
}
TEST(IdletimerEventTest, LegacyActiveWithoutOptionalMetadata) {
    auto event = decode({"SUBSYSTEM=xt_idletimer", "LABEL=1", "STATE=active"});
    ASSERT_TRUE(event); EXPECT_EQ(1, event->label); EXPECT_TRUE(event->active);
    EXPECT_EQ(0, event->timestamp); EXPECT_EQ(-1, event->uid);
}
TEST(IdletimerEventTest, LegacyInactive) {
    auto event = decode({"LABEL=1", "STATE=inactive"});
    ASSERT_TRUE(event); EXPECT_FALSE(event->active); EXPECT_EQ(-1, event->uid);
}
TEST(IdletimerEventTest, ModernMetadataPreserved) {
    auto event = decode({"INTERFACE=2", "STATE=active", "TIME_NS=1234567890", "UID=10123"});
    ASSERT_TRUE(event); EXPECT_EQ(2, event->label); EXPECT_TRUE(event->active);
    EXPECT_EQ(1234567890, event->timestamp); EXPECT_EQ(10123, event->uid);
}
TEST(IdletimerEventTest, ModernLabelTakesPrecedence) {
    auto event = decode({"INTERFACE=2", "LABEL=1", "STATE=inactive", "UID=10123"});
    ASSERT_TRUE(event); EXPECT_EQ(2, event->label); EXPECT_EQ(-1, event->uid);
}
TEST(IdletimerEventTest, MissingLabelRejected) { EXPECT_FALSE(decode({"STATE=active"})); }
TEST(IdletimerEventTest, MissingStateRejected) { EXPECT_FALSE(decode({"LABEL=1"})); }
TEST(IdletimerEventTest, NonIntegerLabelRejected) { EXPECT_FALSE(decode({"LABEL=wlan0", "STATE=active"})); }
TEST(IdletimerEventTest, OverflowRejected) { EXPECT_FALSE(decode({"LABEL=2147483648", "STATE=active"})); }
}  // namespace android::net
