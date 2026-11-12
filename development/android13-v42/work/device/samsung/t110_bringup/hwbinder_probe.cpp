// Diagnostic only: claims the otherwise unused /dev/hwbinder context.
// Tests Android 13's actual HIDL Binder implementation (inside libhidlbase),
// including a scatter/gather buffer in each direction, not a synthetic ioctl.
#include <hwbinder/Binder.h>
#include <hwbinder/IPCThreadState.h>
#include <hwbinder/Parcel.h>
#include <hwbinder/ProcessState.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

using android::BAD_VALUE;
using android::OK;
using android::sp;
using android::status_t;
using namespace android::hardware;

constexpr size_t kSize = 4099;
static uint8_t pattern(size_t i) { return static_cast<uint8_t>(i * 17 + 3); }

class Echo final : public BHwBinder {
    status_t onTransact(uint32_t code, const Parcel& data, Parcel* reply,
                        uint32_t flags, TransactCallback callback) override {
        if (code != FIRST_CALL_TRANSACTION)
            return BHwBinder::onTransact(code, data, reply, flags, callback);
        int32_t token = 0;
        size_t handle = 0;
        const void* input = nullptr;
        if (!reply || !callback || data.readInt32(&token) != OK || token != 0x2468 ||
            data.readBuffer(kSize, &handle, &input) != OK || !input) return BAD_VALUE;
        uint8_t output[kSize];
        for (size_t i = 0; i < kSize; ++i) {
            if (static_cast<const uint8_t*>(input)[i] != pattern(i)) return BAD_VALUE;
            output[i] = pattern(i) ^ 0x5a;
        }
        if (reply->writeInt32(getpid()) != OK ||
            reply->writeBuffer(output, sizeof(output), &handle) != OK) return BAD_VALUE;
        callback(*reply);  // Send while output is still alive.
        return OK;
    }
};

int main() {
    if (getuid() != 0 || access("/t110-native-diagnostic", F_OK) ||
        access("/dev/hwbinder", R_OK | W_OK)) {
        fprintf(stderr, "Run only in the T110 RAM-only diagnostic; never on a full OS\n");
        return 2;
    }
    int ready[2];
    if (pipe(ready)) return 2;
    alarm(20);
    const pid_t server = fork();
    if (server < 0) return 2;
    if (!server) {
        close(ready[0]);
        alarm(20);
        auto process = ProcessState::self();
        IPCThreadState::self()->setTheContextObject(sp<Echo>::make());
        process->becomeContextManager();
        if (write(ready[1], "Y", 1) != 1) _exit(3);
        close(ready[1]);
        IPCThreadState::self()->joinThreadPool();
        _exit(4);
    }
    close(ready[1]);
    char ready_byte = 0;
    int result = 1;
    if (read(ready[0], &ready_byte, 1) == 1 && ready_byte == 'Y') {
        auto remote = ProcessState::self()->getContextObject(nullptr);
        uint8_t input[kSize];
        for (size_t i = 0; i < kSize; ++i) input[i] = pattern(i);
        Parcel request, reply;
        size_t handle = 0;
        int32_t server_pid = 0;
        const void* output = nullptr;
        if (remote && request.writeInt32(0x2468) == OK &&
            request.writeBuffer(input, sizeof(input), &handle) == OK &&
            remote->transact(IBinder::FIRST_CALL_TRANSACTION, request, &reply) == OK &&
            reply.readInt32(&server_pid) == OK && server_pid == server &&
            reply.readBuffer(kSize, &handle, &output) == OK && output) {
            result = 0;
            for (size_t i = 0; i < kSize; ++i)
                if (static_cast<const uint8_t*>(output)[i] != (pattern(i) ^ 0x5a)) result = 1;
        }
    }
    close(ready[0]);
    kill(server, SIGKILL);
    waitpid(server, nullptr, 0);
    alarm(0);
    printf("%s Android 13 HIDL Binder cross-process 4099-byte SG roundtrip\n", result ? "FAIL" : "PASS");
    return result;
}
