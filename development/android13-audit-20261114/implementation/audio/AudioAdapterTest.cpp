/* SPDX-License-Identifier: Apache-2.0 */
#include "LegacyDevice.h"
#include <cassert>
#include <cstring>
#include <cstdlib>
#include <string>
#include <cstdio>

namespace {
using t110::LegacyDevice;using t110::LegacyConfig;
LegacyDevice* expectedDevice;
audio_stream_out* originalOut=nullptr;audio_stream_in* originalIn=nullptr;
std::string lastOutput,lastInput;int closes=0,outputCloses=0,inputCloses=0,reads=0,writes=0;
bool active=false,failActive=false;
uint32_t rate(const audio_stream*){return 44100;}
size_t bufferSize(const audio_stream*){return 1024;}
audio_channel_mask_t channels(const audio_stream*){return AUDIO_CHANNEL_OUT_STEREO;}
audio_format_t format(const audio_stream*){return AUDIO_FORMAT_PCM_16_BIT;}
int standby(audio_stream*){return 0;}
char* streamGet(const audio_stream*,const char*){return strdup("");}
int outParams(audio_stream* s,const char* p){assert(s==&originalOut->common);lastOutput=p;return 0;}
int inParams(audio_stream* s,const char* p){assert(s==&originalIn->common);lastInput=p;std::string q=p;if(q.find("STREAM_IN_ACTIVE=1")!=std::string::npos){if(failActive)return -EIO;active=true;}if(q.find("STREAM_IN_ACTIVE=0")!=std::string::npos)active=false;return 0;}
uint32_t latency(const audio_stream_out*){return 23;}
ssize_t write(audio_stream_out* s,const void*,size_t n){assert(s==originalOut);++writes;return n;}
ssize_t read(audio_stream_in* s,void* p,size_t n){assert(s==originalIn&&active);++reads;memset(p,0x3a,n);return n;}
void common(audio_stream& s){s.get_sample_rate=rate;s.get_buffer_size=bufferSize;s.get_channels=channels;s.get_format=format;s.standby=standby;s.get_parameters=streamGet;}
int close(hw_device_t* d){assert(d==&expectedDevice->common);++closes;return 0;}
int init(const LegacyDevice* d){assert(d==expectedDevice);return 0;}
int mic(LegacyDevice*,bool){return 0;}
int getMic(const LegacyDevice*,bool* v){*v=false;return 0;}
int params(LegacyDevice*,const char*){return 0;}
char* getParams(const LegacyDevice*,const char*){return strdup("");}
size_t inputSize(const LegacyDevice*,const LegacyConfig* c){assert(c->sample_rate==44100);return 4096;}
int dump(const LegacyDevice* d,int fd){assert(d==expectedDevice);return fd+100;}
int outOpen(LegacyDevice* d,audio_io_handle_t,audio_devices_t,audio_output_flags_t,LegacyConfig* c,audio_stream_out** out){assert(d==expectedDevice&&c->sample_rate==44100);originalOut=static_cast<audio_stream_out*>(calloc(1,offsetof(audio_stream_out,set_callback)));common(originalOut->common);originalOut->common.set_parameters=outParams;originalOut->get_latency=latency;originalOut->write=write;*out=originalOut;return 0;}
void outClose(LegacyDevice* d,audio_stream_out* out){assert(d==expectedDevice&&out==originalOut);free(out);originalOut=nullptr;++outputCloses;}
int inOpen(LegacyDevice* d,audio_io_handle_t,audio_devices_t,LegacyConfig*,audio_stream_in** in){assert(d==expectedDevice);originalIn=static_cast<audio_stream_in*>(calloc(1,offsetof(audio_stream_in,get_capture_position)));common(originalIn->common);originalIn->common.set_parameters=inParams;originalIn->read=read;*in=originalIn;return 0;}
void inClose(LegacyDevice* d,audio_stream_in* in){assert(d==expectedDevice&&in==originalIn&&!active);free(in);originalIn=nullptr;++inputCloses;}
}
int main(){
 hw_module_t module{};module.tag=HARDWARE_MODULE_TAG;module.module_api_version=AUDIO_MODULE_API_VERSION_0_1;module.id=AUDIO_HARDWARE_MODULE_ID;module.name="Marvll audio HW HAL";module.author="Marvell APSE/PIE";
 LegacyDevice old{};expectedDevice=&old;old.common.tag=HARDWARE_DEVICE_TAG;old.common.version=AUDIO_DEVICE_API_VERSION_2_0;old.common.module=&module;old.common.close=close;
 old.init_check=init;old.set_mic_mute=mic;old.get_mic_mute=getMic;old.set_parameters=params;old.get_parameters=getParams;old.get_input_buffer_size=inputSize;old.open_output_stream=outOpen;old.close_output_stream=outClose;old.open_input_stream=inOpen;old.close_input_stream=inClose;old.dump=dump;
 audio_hw_device_t* modern=nullptr;
 module.author="Other vendor";assert(t110::adaptDevice(&old,&modern)==-EINVAL&&!modern);module.author="Marvell APSE/PIE";
 assert(t110::adaptDevice(&old,&modern)==0&&modern->common.version==AUDIO_DEVICE_API_VERSION_2_0);
 assert(modern->init_check(modern)==0&&modern->dump(modern,7)==107&&modern->get_microphones==nullptr&&modern->create_audio_patch==nullptr);
 audio_config c{};c.sample_rate=48000;c.channel_mask=AUDIO_CHANNEL_OUT_STEREO;c.format=AUDIO_FORMAT_PCM_16_BIT;
 audio_stream_out* out=nullptr;assert(modern->open_output_stream(modern,1,AUDIO_DEVICE_OUT_SPEAKER,AUDIO_OUTPUT_FLAG_PRIMARY,&c,&out,"")==-EINVAL&&c.sample_rate==44100&&!out);
 assert(modern->open_output_stream(modern,1,AUDIO_DEVICE_OUT_SPEAKER,AUDIO_OUTPUT_FLAG_PRIMARY,&c,&out,"")==0);
 assert(out->set_callback==nullptr&&out->update_source_metadata_v7==nullptr&&out->get_latency(out)==23);
 uint32_t frames=0;assert(out->get_render_position(out,&frames)==-ENOSYS);
 assert(out->common.dump(&out->common,1)==-ENOSYS&&out->common.set_sample_rate(&out->common,44100)==-ENOSYS);
 assert(modern->common.close(&modern->common)==-EBUSY);
 out->common.set_parameters(&out->common,"routing=2;custom=hello");assert(lastOutput.find("path_handler=0")!=std::string::npos&&lastOutput.find("phone_volume=230")!=std::string::npos&&lastOutput.find("custom=hello")!=std::string::npos);
 out->common.set_parameters(&out->common,"routing=2;path_handler=8;phone_volume=17");assert(lastOutput.find("path_handler=8")!=std::string::npos&&lastOutput.find("phone_volume=17")!=std::string::npos);
 out->common.set_parameters(&out->common,"routing=128");assert(lastOutput.find("path_handler")==std::string::npos);
 char bytes[32]{};assert(out->write(out,bytes,sizeof(bytes))==sizeof(bytes)&&writes==1);
 modern->close_output_stream(modern,out);assert(outputCloses==1);
 audio_stream_in* in=nullptr;c.channel_mask=AUDIO_CHANNEL_IN_MONO;
 assert(modern->open_input_stream(modern,2,AUDIO_DEVICE_IN_BUILTIN_MIC,&c,&in,AUDIO_INPUT_FLAG_NONE,"",AUDIO_SOURCE_MIC)==0);
 assert(in->get_capture_position==nullptr&&in->update_sink_metadata_v7==nullptr);
 assert(in->get_input_frames_lost(in)==0&&in->common.add_audio_effect(&in->common,nullptr)==-ENOSYS);
 failActive=true;assert(in->read(in,bytes,sizeof(bytes))==-EIO&&reads==0&&!active);
 failActive=false;assert(in->read(in,bytes,sizeof(bytes))==sizeof(bytes)&&active&&reads==1&&bytes[0]==0x3a);
 assert(in->common.standby(&in->common)==0&&!active);
 assert(in->read(in,bytes,sizeof(bytes))==sizeof(bytes)&&active&&reads==2);
 modern->close_input_stream(modern,in);assert(inputCloses==1&&!active);
 assert(modern->common.close(&modern->common)==0&&closes==1);
 puts("PASS: real audio proxy routing/ABI/rate/callback bounds/activation/error/standby/close cases");
}
