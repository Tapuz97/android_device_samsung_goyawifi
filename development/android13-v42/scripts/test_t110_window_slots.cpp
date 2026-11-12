#include "../work/T110WindowSlots.h"
#include <cassert>
#include <iostream>
using android::renderengine::gl::T110WindowSlots;
int main() {
    // EGL can pre-dequeue multiple buffers. Only the first, caller-owned
    // target may be published; post-swap acquisition must never recycle it.
    T110WindowSlots slots;
    assert(!slots.published());
    assert(!slots.queue(0));
    assert(!slots.cancel(0));
    assert(slots.dequeue() == 0);
    assert(slots.dequeue() == 1);
    assert(slots.dequeue() == -1); // Preserve the declared consumer reservation.
    assert(!slots.configure(2));
    assert(!slots.queue(1));
    assert(slots.queue(0));
    assert(slots.published());
    assert(!slots.queue(0));
    assert(!slots.cancel(0));
    assert(slots.dequeue() == 2);
    assert(slots.dequeue() == -1);
    assert(slots.cancel(1));
    assert(slots.dequeue() == 1);
    assert(slots.cancel(2));
    assert(slots.cancel(1));
    assert(!slots.cancel(3));
    assert(!slots.queue(3));
    T110WindowSlots doubleBuffered;
    assert(doubleBuffered.configure(2));
    assert(!doubleBuffered.configure(1));
    assert(doubleBuffered.dequeue() == 0);
    assert(doubleBuffered.dequeue() == -1);
    assert(doubleBuffered.queue(0));
    assert(doubleBuffered.dequeue() == 1);
    assert(doubleBuffered.dequeue() == -1);
    assert(doubleBuffered.cancel(1));
    assert(doubleBuffered.dequeue() == 1);
    for (int i = 0; i != 10000; ++i) {
        T110WindowSlots aborted;
        assert(aborted.dequeue() == 0);
        assert(aborted.cancel(0));
        assert(!aborted.published());
        assert(aborted.dequeue() == 0);
        assert(aborted.queue(0));
        assert(aborted.dequeue() == 1);
    }
    std::cout << "PASS: EGL target ownership, pre-dequeue, cancellation, spare rotation, invalid transitions\n";
}
