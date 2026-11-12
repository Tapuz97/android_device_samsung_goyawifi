// One-shot EGL window ownership. A queued target is never recycled into EGL.
#pragma once
#include <array>
#include <cstddef>

namespace android::renderengine::gl {
class T110WindowSlots {
public:
    static constexpr size_t kCount = 3;
    bool configure(size_t count) {
        if (count < 2 || count > kCount) return false;
        for (auto state : mSlots) if (state != State::Available) return false;
        mCount = count;
        return true;
    }
    int dequeue() {
        size_t held = 0;
        for (auto state : mSlots) if (state == State::Dequeued) ++held;
        if (held >= mCount - 1) return -1; // One consumer-reserved slot.
        for (size_t i = 0; i != mCount; ++i) {
            if (mSlots[i] == State::Available) {
                mSlots[i] = State::Dequeued;
                return static_cast<int>(i);
            }
        }
        return -1;
    }
    bool queue(size_t slot) {
        if (slot >= kCount || mSlots[slot] != State::Dequeued) return false;
        // This window publishes exactly one frame: the caller's target.
        if (slot != 0 || mPublished) return false;
        mSlots[slot] = State::Queued;
        mPublished = true;
        return true;
    }
    bool cancel(size_t slot) {
        if (slot >= kCount || mSlots[slot] != State::Dequeued) return false;
        mSlots[slot] = State::Available;
        return true;
    }
    bool dequeued(size_t slot) const {
        return slot < kCount && mSlots[slot] == State::Dequeued;
    }
    bool published() const { return mPublished; }
private:
    enum class State { Available, Dequeued, Queued };
    std::array<State, kCount> mSlots{};
    bool mPublished = false;
    size_t mCount = kCount;
};
} // namespace android::renderengine::gl
