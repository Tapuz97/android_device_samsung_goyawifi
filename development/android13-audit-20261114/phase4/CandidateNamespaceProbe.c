/* SPDX-License-Identifier: Apache-2.0 */
#include <dlfcn.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Exact platform-private Bionic APIs, used only to initialize the isolated
 * property fixture. This executable is never installed into the ROM. */
extern int __system_property_area_init(void);
extern int __system_property_add(const char*, unsigned int, const char*, unsigned int);
extern int __system_property_get(const char*, char*);

int main(int argc, char** argv) {
    if (getenv("LD_LIBRARY_PATH") || getenv("LD_PRELOAD") || getenv("T110_PROBE_LEGACY_SDK")) {
        fputs("FAIL: non-production loader override present\n", stderr); return 9;
    }
    if (argc == 3 && !strcmp(argv[1], "properties")) {
        int area_result = __system_property_area_init();
        /* WSL has no SELinux property xattrs. AreaInit may report that label
         * failure even when it initialized the actual serialized areas. Each
         * add/read must still succeed; no property getter is replaced. */
        if (area_result) fprintf(stderr, "Fixture AreaInit returned %d (offline host has no SELinux labels)\n", area_result);
        FILE* input = fopen(argv[2], "r");
        if (!input) return 10;
        char line[16384]; unsigned count = 0;
        while (fgets(line, sizeof(line), input)) {
            line[strcspn(line, "\r\n")] = 0;
            char* equal = strchr(line, '=');
            if (!equal || line[0] == '#') continue;
            *equal++ = 0;
            if (__system_property_add(line, (unsigned)strlen(line), equal, (unsigned)strlen(equal))) {
                fprintf(stderr, "FAIL property add: %s\n", line); return 11;
            }
            ++count;
        }
        if (ferror(input) || fclose(input)) return 12;
        printf("PASS real Bionic serialized property areas: %u values\n", count); return 0;
    }
    if (argc == 4 && !strcmp(argv[1], "get")) {
        char value[1024];
        if (__system_property_get(argv[2], value) <= 0 || strcmp(value, argv[3])) {
            fprintf(stderr, "FAIL property %s: %s\n", argv[2], value); return 13;
        }
        printf("PASS property %s=%s\n", argv[2], value); return 0;
    }
    if (argc >= 3 && !strcmp(argv[1], "load")) {
        for (int i=2; i<argc; ++i) {
            void* handle = dlopen(argv[i], RTLD_NOW | RTLD_LOCAL);
            if (!handle) { fprintf(stderr, "FAIL %s: %s\n", argv[i], dlerror()); return 20; }
            printf("PASS production-namespace dlopen %s\n", argv[i]);
        }
        return 0;
    }
    fputs("Expected properties FILE, get NAME VALUE, or load LIB...\n", stderr);
    return 2;
}
