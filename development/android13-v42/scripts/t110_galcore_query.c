/* Read the 3D core identity using the ABI of the archived T110 galcore.ko. */
#include <fcntl.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <sys/ioctl.h>
#include <unistd.h>

/* Sizes and offsets come from the module's DWARF, not a newer Vivante header. */
struct galcore_query {
    uint32_t command;
    uint32_t hardware_type;
    int32_t status;
    uint32_t handle;
    uint32_t pid;
    uint32_t alignment_padding;
    uint32_t model;
    uint32_t revision;
    uint32_t features;
    uint32_t minor_features;
    uint8_t unused[120];
};

struct galcore_args {
    void *input;
    uint32_t input_size;
    void *output;
    uint32_t output_size;
};

_Static_assert(sizeof(struct galcore_query) == 160, "gcsHAL_INTERFACE size");
_Static_assert(offsetof(struct galcore_query, model) == 24, "QueryChipIdentity offset");
_Static_assert(sizeof(struct galcore_args) == 16, "DRIVER_ARGS size");

int main(void)
{
    if (access("/t110-native-diagnostic", F_OK)) {
        fprintf(stderr, "Run only in the T110 RAM diagnostic\n");
        return 2;
    }
    int fd = open("/dev/galcore", O_RDWR | O_CLOEXEC);
    if (fd < 0) {
        perror("open galcore");
        return 1;
    }
    struct galcore_query query = {
        .command = 1,        /* gcvHAL_QUERY_CHIP_IDENTITY */
        .hardware_type = 1,  /* gcvHARDWARE_3D */
        .status = -1,
        .pid = (uint32_t)getpid(),
    };
    struct galcore_args args = {&query, sizeof(query), &query, sizeof(query)};
    if (ioctl(fd, 30000, &args) < 0) {  /* IOCTL_GCHAL_INTERFACE */
        perror("query galcore identity");
        close(fd);
        return 1;
    }
    close(fd);
    printf("galcore status=%d model=%#x revision=%#x features=%#x minor_features=%#x\n",
           query.status, query.model, query.revision, query.features, query.minor_features);
    return query.status || !query.model ? 1 : 0;
}
