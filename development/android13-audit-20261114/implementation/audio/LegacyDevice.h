/* SPDX-License-Identifier: Apache-2.0 */
#pragma once
#include <hardware/audio.h>
#include <cstddef>

namespace t110 {
// Exact API2 ANI7 prefix; Android13 inserted get_microphones before dump.
// Never interpret the original vendor allocation as a full modern device.
struct LegacyConfig {
    uint32_t sample_rate;
    audio_channel_mask_t channel_mask;
    audio_format_t format;
    uint32_t frame_count;
};
struct LegacyDevice {
    hw_device_t common;
    uint32_t (*get_supported_devices)(const LegacyDevice*);
    int (*init_check)(const LegacyDevice*);
    int (*set_voice_volume)(LegacyDevice*,float);
    int (*set_master_volume)(LegacyDevice*,float);
    int (*get_master_volume)(LegacyDevice*,float*);
    int (*set_mode)(LegacyDevice*,audio_mode_t);
    int (*set_mic_mute)(LegacyDevice*,bool);
    int (*get_mic_mute)(const LegacyDevice*,bool*);
    int (*set_parameters)(LegacyDevice*,const char*);
    char* (*get_parameters)(const LegacyDevice*,const char*);
    size_t (*get_input_buffer_size)(const LegacyDevice*,const LegacyConfig*);
    int (*open_output_stream)(LegacyDevice*,audio_io_handle_t,audio_devices_t,
                             audio_output_flags_t,LegacyConfig*,audio_stream_out**);
    void (*close_output_stream)(LegacyDevice*,audio_stream_out*);
    int (*open_input_stream)(LegacyDevice*,audio_io_handle_t,audio_devices_t,
                            LegacyConfig*,audio_stream_in**);
    void (*close_input_stream)(LegacyDevice*,audio_stream_in*);
    int (*dump)(const LegacyDevice*,int);
};
#if defined(__arm__) && !defined(__LP64__)
static_assert(sizeof(hw_device_t)==64,"ANI7 hw device prefix");
static_assert(offsetof(LegacyDevice,open_output_stream)==108,"ANI7 output open");
static_assert(offsetof(LegacyDevice,open_input_stream)==116,"ANI7 input open");
static_assert(offsetof(LegacyDevice,dump)==124,"ANI7 dump");
static_assert(sizeof(LegacyDevice)==128,"ANI7 public device prefix");
static_assert(offsetof(audio_hw_device,dump)!=offsetof(LegacyDevice,dump),"Modern device must be adapted");
static_assert(sizeof(LegacyConfig)==16,"ANI7 configuration prefix");
#endif
int adaptDevice(LegacyDevice*, audio_hw_device_t**);
}
