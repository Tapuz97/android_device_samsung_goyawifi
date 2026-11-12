// SPDX-License-Identifier: Apache-2.0
// Marvell SD8777 character transport; shared firmware is initialized by the kernel.
#define LOG_TAG "bt-vendor-t110"
#include "bt_vendor_lib.h"
#include <errno.h>
#include <fcntl.h>
#include <log/log.h>
#include <stddef.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static const bt_vendor_callbacks_t* callbacks;
static int transport_fd=-1;
static void close_transport(void) {
    if(transport_fd>=0)close(transport_fd);
    transport_fd=-1;
}
static int init(const bt_vendor_callbacks_t* cb,unsigned char* address) {
    (void)address; // Preserve the controller's identity; never program a generated address.
    if(!cb || cb->size<sizeof(*cb) || !cb->fwcfg_cb || !cb->lpm_cb)return -EINVAL;
    if(callbacks)return -EBUSY;
    callbacks=cb;return 0;
}
static int op(bt_vendor_opcode_t opcode,void* param) {
    if(!callbacks)return -ENODEV;
    switch(opcode) {
    case BT_VND_OP_POWER_CTRL:
        if(!param)return -EINVAL;
        if(*(int*)param==BT_VND_PWR_OFF){close_transport();return 0;}
        // GPIO/firmware power is shared with Wi-Fi and owned by the board driver.
        return *(int*)param==BT_VND_PWR_ON ? 0 : -EINVAL;
    case BT_VND_OP_USERIAL_OPEN: {
        if(!param || transport_fd>=0)return 0;
        int* fds=param;for(int i=0;i<CH_MAX;++i)fds[i]=-1;
        int fd=open("/dev/mbtchar0",O_RDWR|O_CLOEXEC|O_NONBLOCK|O_NOFOLLOW);
        if(fd<0){ALOGE("open Marvell character transport: %s",strerror(errno));return 0;}
        struct stat st;
        if(fstat(fd,&st) || !S_ISCHR(st.st_mode) || (st.st_mode&0007)){close(fd);return 0;}
        transport_fd=fd;fds[CH_CMD]=fd;return 1;
    }
    case BT_VND_OP_USERIAL_CLOSE:close_transport();return 0;
    case BT_VND_OP_FW_CFG:
        // Kernel module bring-up already completed on the active combo firmware.
        callbacks->fwcfg_cb(transport_fd>=0?BT_VND_OP_RESULT_SUCCESS:BT_VND_OP_RESULT_FAIL);return 0;
    case BT_VND_OP_GET_LPM_IDLE_TIMEOUT:
        if(!param)return -EINVAL;
        *(uint32_t*)param=1000;return 0;
    case BT_VND_OP_LPM_SET_MODE:
        // The SDIO driver owns firmware wake/sleep; there is no UART wake GPIO.
        if(!param)return -EINVAL;
        callbacks->lpm_cb(BT_VND_OP_RESULT_SUCCESS);return 0;
    case BT_VND_OP_LPM_WAKE_SET_STATE:return param?0:-EINVAL;
    case BT_VND_OP_EPILOG:
        if(callbacks->epilog_cb)callbacks->epilog_cb(BT_VND_OP_RESULT_SUCCESS);
        return 0;
    case BT_VND_OP_SCO_CFG:
        if(callbacks->scocfg_cb)callbacks->scocfg_cb(BT_VND_OP_RESULT_FAIL);
        return -ENOTSUP;
    case BT_VND_OP_SET_AUDIO_STATE:
        if(callbacks->audio_state_cb)callbacks->audio_state_cb(BT_VND_OP_RESULT_FAIL);
        return -ENOTSUP;
    case BT_VND_OP_A2DP_OFFLOAD_START:
    case BT_VND_OP_A2DP_OFFLOAD_STOP:
        if(callbacks->a2dp_offload_cb)callbacks->a2dp_offload_cb(BT_VND_OP_RESULT_FAIL,opcode,0);
        return -ENOTSUP;
    default:return -ENOTSUP;
    }
}
static void cleanup(void){close_transport();callbacks=NULL;}
const bt_vendor_interface_t BLUETOOTH_VENDOR_LIB_INTERFACE={sizeof(bt_vendor_interface_t),init,op,cleanup};
