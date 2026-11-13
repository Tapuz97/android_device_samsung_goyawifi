"""Translate local HiFi routing for the exact ANI7 HAL's old policy protocol."""
from pathlib import Path
p=Path('/root/t110-lineage14/android/frameworks/av/services/audioflinger/T110AudioStreamCompat.h')
s=p.read_text()
anchor='''struct Output {
    static audio_stream_out* original'''
replacement='''struct Output {
    static int set_parameters(audio_stream* common, const char* pairs) {
        audio_stream_out* s = reinterpret_cast<audio_stream_out*>(common);
        AudioParameter parameters{String8(pairs)};
        int route;
        const audio_devices_t local = AUDIO_DEVICE_OUT_SPEAKER |
                AUDIO_DEVICE_OUT_WIRED_HEADSET | AUDIO_DEVICE_OUT_WIRED_HEADPHONE;
        if (parameters.getInt(String8(AUDIO_PARAMETER_STREAM_ROUTING), route) == NO_ERROR &&
                ((audio_devices_t)route & ~local) == 0) {
            // ANI7 out_set_parameters skips routing unless BOTH keys exist.
            // Its path table maps 0 to hifi. Stock policy uses phone_volume=230
            // outside calls; stream attenuation remains AudioFlinger's job.
            int existing;
            if (parameters.getInt(String8("path_handler"), existing) != NO_ERROR)
                parameters.addInt(String8("path_handler"), 0);
            if (parameters.getInt(String8("phone_volume"), existing) != NO_ERROR)
                parameters.addInt(String8("phone_volume"), 230);
        }
        return original(s)->common.set_parameters(
                &original(s)->common, parameters.toString().string());
    }
    static audio_stream_out* original'''
if replacement not in s:
    assert s.count(anchor)==1
    s=s.replace(anchor,replacement)
anchor='''        Common<audio_stream_out>::initialize(p);
        if (originalStream->get_latency)'''
replacement='''        Common<audio_stream_out>::initialize(p);
        p->stream.common.set_parameters = set_parameters;
        if (originalStream->get_latency)'''
if replacement not in s:
    assert s.count(anchor)==1
    s=s.replace(anchor,replacement)
p.write_text(s)
print('Restored stock local HiFi path-selection parameters in ANI7 output proxy.')
