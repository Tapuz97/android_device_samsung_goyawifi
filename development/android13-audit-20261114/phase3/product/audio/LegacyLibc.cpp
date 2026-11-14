/* SPDX-License-Identifier: Apache-2.0 */
#include <dlfcn.h>
#include <cstdlib>

// Exact private ABI used by this device's stock audio binaries. An explicit
// libc handle avoids RTLD_NEXT ordering and accidental recursion into our shim.
extern "C" __attribute__((visibility("hidden")))
void* t110_resolve_legacy_libc(const char* name, void** slot) {
    static void* const libc = dlopen("libc.so", RTLD_NOW | RTLD_LOCAL);
    if (!libc) std::abort();
    void* const target = dlsym(libc, name);
    if (!target) std::abort();
    __atomic_store_n(slot, target, __ATOMIC_RELEASE);
    return target;
}
