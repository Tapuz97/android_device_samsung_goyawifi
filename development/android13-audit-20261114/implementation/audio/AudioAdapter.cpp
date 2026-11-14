/* SPDX-License-Identifier: Apache-2.0 */
#define T110_MRVL_LEGACY 1
#include "LegacyDevice.h"
#include "StreamCompat.h"
#include <atomic>
#include <cstring>
#include <new>

namespace t110 {
using android::t110_audio_compat::Input;
using android::t110_audio_compat::Output;
struct Adapter {
    audio_hw_device_t device{};
    LegacyDevice* legacy=nullptr;
    std::atomic<unsigned> streams{0};
};
static Adapter* adapter(const audio_hw_device_t* d) {
    return reinterpret_cast<Adapter*>(const_cast<audio_hw_device_t*>(d));
}
static LegacyDevice* legacy(const audio_hw_device_t* d) { return adapter(d)->legacy; }
static bool validCommon(const audio_stream& s) {
    return s.get_sample_rate&&s.get_buffer_size&&s.get_channels&&s.get_format&&
           s.standby&&s.set_parameters&&s.get_parameters;
}
static LegacyConfig legacyConfig(const audio_config& c) {
    return {c.sample_rate,c.channel_mask,c.format,0};
}
static void suggestedConfig(audio_config& out,const LegacyConfig& c) {
    out.sample_rate=c.sample_rate;out.channel_mask=c.channel_mask;out.format=c.format;
    if(c.frame_count)out.frame_count=c.frame_count;
}
static int close(hw_device_t* device) {
    auto* a=reinterpret_cast<Adapter*>(device);
    if(a->streams.load()!=0)return -EBUSY;
    int result=a->legacy->common.close(&a->legacy->common);
    if(!result)delete a;
    return result;
}
static int init(const audio_hw_device_t* d){return legacy(d)->init_check(legacy(d));}
static int voice(audio_hw_device_t* d,float v){auto*l=legacy(d);return l->set_voice_volume?l->set_voice_volume(l,v):-ENOSYS;}
static int master(audio_hw_device_t* d,float v){auto*l=legacy(d);return l->set_master_volume?l->set_master_volume(l,v):-ENOSYS;}
static int getMaster(audio_hw_device_t* d,float* v){auto*l=legacy(d);return l->get_master_volume?l->get_master_volume(l,v):-ENOSYS;}
static int mode(audio_hw_device_t* d,audio_mode_t v){auto*l=legacy(d);return l->set_mode?l->set_mode(l,v):-ENOSYS;}
static int mic(audio_hw_device_t* d,bool v){return legacy(d)->set_mic_mute(legacy(d),v);}
static int getMic(const audio_hw_device_t* d,bool* v){return legacy(d)->get_mic_mute(legacy(d),v);}
static int parameters(audio_hw_device_t* d,const char* p){return p?legacy(d)->set_parameters(legacy(d),p):-EINVAL;}
static char* getParameters(const audio_hw_device_t* d,const char* p){return p?legacy(d)->get_parameters(legacy(d),p):nullptr;}
static size_t inputSize(const audio_hw_device_t* d,const audio_config* c){if(!c)return 0;auto config=legacyConfig(*c);return legacy(d)->get_input_buffer_size(legacy(d),&config);}
static int dump(const audio_hw_device_t* d,int fd){auto*l=legacy(d);return l->dump?l->dump(l,fd):-ENOSYS;}
static int openOutput(audio_hw_device_t* d,audio_io_handle_t handle,audio_devices_t devices,
                      audio_output_flags_t flags,audio_config* config,audio_stream_out** out,const char*) {
    if(!config||!out)return -EINVAL;
    *out=nullptr;
    // Measured ANI7 rejection is not the standard -EINVAL suggested-config flow.
    if(config->sample_rate!=44100){config->sample_rate=44100;return -EINVAL;}
    auto c=legacyConfig(*config);audio_stream_out* original=nullptr;
    auto*l=legacy(d);
    int error=l->open_output_stream(l,handle,devices,flags,&c,&original);
    suggestedConfig(*config,c);
    if(error){if(original)l->close_output_stream(l,original);return error;}
    if(!original)return -ENODEV;
    if(!validCommon(original->common)||!original->write||!original->get_latency) {
        l->close_output_stream(l,original);return -EINVAL;
    }
    *out=Output::wrap(original);
    if(!*out){l->close_output_stream(l,original);return -ENOMEM;}
    ++adapter(d)->streams;return 0;
}
static void closeOutput(audio_hw_device_t* d,audio_stream_out* out) {
    if(!out)return;
    legacy(d)->close_output_stream(legacy(d),Output::unwrapAndDestroy(out));
    --adapter(d)->streams;
}
static int openInput(audio_hw_device_t* d,audio_io_handle_t handle,audio_devices_t devices,
                     audio_config* config,audio_stream_in** in,audio_input_flags_t,
                     const char*,audio_source_t) {
    if(!config||!in)return -EINVAL;
    *in=nullptr;auto c=legacyConfig(*config);audio_stream_in* original=nullptr;
    auto*l=legacy(d);int error=l->open_input_stream(l,handle,devices,&c,&original);
    suggestedConfig(*config,c);
    if(error){if(original)l->close_input_stream(l,original);return error;}
    if(!original)return -ENODEV;
    if(!validCommon(original->common)||!original->read) {
        l->close_input_stream(l,original);return -EINVAL;
    }
    *in=Input::wrap(original,devices);
    if(!*in){l->close_input_stream(l,original);return -ENOMEM;}
    ++adapter(d)->streams;return 0;
}
static void closeInput(audio_hw_device_t* d,audio_stream_in* in) {
    if(!in)return;
    // Close must send STREAM_IN_ACTIVE=0 even if no final framework standby ran.
    in->common.standby(&in->common);
    legacy(d)->close_input_stream(legacy(d),Input::unwrapAndDestroy(in));
    --adapter(d)->streams;
}
int adaptDevice(LegacyDevice* original,audio_hw_device_t** out) {
    if(!out)return -EINVAL;
    *out=nullptr;
    if(!original||!original->common.module)return -EINVAL;
    auto* module=original->common.module;
    if(original->common.tag!=HARDWARE_DEVICE_TAG||original->common.version!=AUDIO_DEVICE_API_VERSION_2_0||
       module->tag!=HARDWARE_MODULE_TAG||module->module_api_version!=AUDIO_MODULE_API_VERSION_0_1||
       !module->id||strcmp(module->id,AUDIO_HARDWARE_MODULE_ID)||
       !module->name||strcmp(module->name,"Marvll audio HW HAL")||
       !module->author||strcmp(module->author,"Marvell APSE/PIE"))return -EINVAL;
    if(!original->common.close||!original->init_check||!original->set_mic_mute||!original->get_mic_mute||
       !original->set_parameters||!original->get_parameters||!original->get_input_buffer_size||
       !original->open_output_stream||!original->close_output_stream||
       !original->open_input_stream||!original->close_input_stream)return -EINVAL;
    auto*a=new(std::nothrow)Adapter;
    if(!a)return -ENOMEM;
    a->legacy=original;
    // Preserve the actual generation; unsupported modern callbacks stay null.
    a->device.common=original->common;a->device.common.close=close;
    a->device.init_check=init;a->device.set_voice_volume=voice;
    a->device.set_master_volume=master;a->device.get_master_volume=getMaster;
    a->device.set_mode=mode;a->device.set_mic_mute=mic;a->device.get_mic_mute=getMic;
    a->device.set_parameters=parameters;a->device.get_parameters=getParameters;
    a->device.get_input_buffer_size=inputSize;a->device.dump=dump;
    a->device.open_output_stream=openOutput;a->device.close_output_stream=closeOutput;
    a->device.open_input_stream=openInput;a->device.close_input_stream=closeInput;
    *out=&a->device;return 0;
}
static_assert(offsetof(Adapter,device)==0,"public device prefix");
}
