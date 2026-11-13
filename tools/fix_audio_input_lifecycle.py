"""Bridge the verified Marvell STREAM_IN_ACTIVE handshake in the stream proxy."""
from pathlib import Path
p=Path('/root/t110-lineage14/android/frameworks/av/services/audioflinger/T110AudioStreamCompat.h')
s=p.read_text()
s=s.replace('#include <hardware/audio.h>','#include <hardware/audio.h>\n#include <media/AudioParameter.h>') if '#include <media/AudioParameter.h>' not in s else s
marker='template<typename Stream> struct Common {'
extra='''// The old input HAL opens/closes PCM via STREAM_IN_ACTIVE, not read/standby.
template<> struct Proxy<audio_stream_in> {
    audio_stream_in stream;
    audio_stream_in* original;
    audio_devices_t routing;
    bool active;
};

'''
if extra not in s:s=s.replace(marker,extra+marker)
old='''    static ssize_t read(audio_stream_in* s, void* buffer, size_t bytes) {
        return original(s)->read(original(s), buffer, bytes);
    }'''
new='''    static int setActive(audio_stream_in* s, bool active) {
        Proxy<audio_stream_in>* p = reinterpret_cast<Proxy<audio_stream_in>*>(s);
        AudioParameter parameters;
        parameters.addInt(String8(AUDIO_PARAMETER_STREAM_ROUTING), (int)p->routing);
        parameters.addInt(String8("STREAM_IN_ACTIVE"), active ? 1 : 0);
        const int result = original(s)->common.set_parameters(
                &original(s)->common, parameters.toString().string());
        if (result == 0) p->active = active;
        return result;
    }
    static int standby(audio_stream* common) {
        audio_stream_in* s = reinterpret_cast<audio_stream_in*>(common);
        Proxy<audio_stream_in>* p = reinterpret_cast<Proxy<audio_stream_in>*>(s);
        if (p->active) {
            const int result = setActive(s, false);
            if (result != 0) return result;
        }
        return original(s)->common.standby(&original(s)->common);
    }
    static int set_parameters(audio_stream* common, const char* pairs) {
        audio_stream_in* s = reinterpret_cast<audio_stream_in*>(common);
        Proxy<audio_stream_in>* p = reinterpret_cast<Proxy<audio_stream_in>*>(s);
        AudioParameter parameters{String8(pairs)};
        int routing;
        const bool hasRoute = parameters.getInt(
                String8(AUDIO_PARAMETER_STREAM_ROUTING), routing) == NO_ERROR;
        if (hasRoute && routing == 0 && p->active) {
            const int result = setActive(s, false);
            if (result != 0) return result;
        }
        if (hasRoute && p->active) parameters.addInt(String8("STREAM_IN_ACTIVE"), 1);
        const int result = original(s)->common.set_parameters(
                &original(s)->common, parameters.toString().string());
        if (result == 0 && hasRoute) p->routing = (audio_devices_t)routing;
        return result;
    }
    static ssize_t read(audio_stream_in* s, void* buffer, size_t bytes) {
        Proxy<audio_stream_in>* p = reinterpret_cast<Proxy<audio_stream_in>*>(s);
        if (!p->active) {
            if (p->routing == AUDIO_DEVICE_NONE) return -ENODEV;
            const int result = setActive(s, true);
            if (result != 0) return result;
        }
        return original(s)->read(original(s), buffer, bytes);
    }'''
if new not in s:
    assert s.count(old)==1
    s=s.replace(old,new)
old='''        Common<audio_stream_in>::initialize(p);
        if (originalStream->set_gain)'''
new='''        Common<audio_stream_in>::initialize(p);
        p->stream.common.standby = standby;
        p->stream.common.set_parameters = set_parameters;
        if (originalStream->set_gain)'''
if new not in s:
    assert s.count(old)==1
    s=s.replace(old,new)
p.write_text(s)
print('Added input activation, route updates and standby to the exact ANI7 proxy.')
