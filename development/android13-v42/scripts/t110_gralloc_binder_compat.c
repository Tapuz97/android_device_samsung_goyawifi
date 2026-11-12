/* Forward the legacy non-const IPCThreadState method to Android 13's const ABI. */
extern int current_get_calling_pid(const void *self)
    __asm__("_ZNK7android14IPCThreadState13getCallingPidEv");
int legacy_get_calling_pid(const void *self)
    __asm__("_ZN7android14IPCThreadState13getCallingPidEv");

int legacy_get_calling_pid(const void *self)
{
    return current_get_calling_pid(self);
}
