/*
 * Copyright 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef T110_AUDIO_STREAM_COMPAT_H
#define T110_AUDIO_STREAM_COMPAT_H
#if defined(T110_MRVL_LEGACY)
#include <hardware/audio.h>
#include "Parameters.h"
#include <new>
#include <stddef.h>
#include <string.h>

// ANI7's stream callback prefixes end before Nougat's optional callbacks.
// Keep private driver state in its original allocation. Every supported call
// receives the original stream, not this separate full-size framework view.
namespace android {
namespace t110_audio_compat {

// Exact ANI7 metadata, including the original vendor's spelling. Do not apply
// legacy bounds to N7-built USB, Bluetooth or other audio HAL implementations.
static inline bool needsAdapter(const audio_hw_device* device) {
    if (!device || device->common.tag != HARDWARE_DEVICE_TAG ||
            device->common.version != AUDIO_DEVICE_API_VERSION_2_0)
        return false;
    const hw_module_t* module = device->common.module;
    return module && module->tag == HARDWARE_MODULE_TAG &&
            module->module_api_version == AUDIO_MODULE_API_VERSION_0_1 &&
            module->id && !strcmp(module->id, AUDIO_HARDWARE_MODULE_ID) &&
            module->name && !strcmp(module->name, "Marvll audio HW HAL") &&
            module->author && !strcmp(module->author, "Marvell APSE/PIE");
}

template<typename Stream> struct Proxy {
    Stream stream;
    Stream* original;
};

// The old input HAL opens/closes PCM via STREAM_IN_ACTIVE, not read/standby.
template<> struct Proxy<audio_stream_in> {
    audio_stream_in stream;
    audio_stream_in* original;
    audio_devices_t routing;
    bool active;
};

template<typename Stream> struct Common {
    static Stream* original(const audio_stream* s) {
        return reinterpret_cast<const Proxy<Stream>*>(s)->original;
    }
    static uint32_t get_sample_rate(const audio_stream* s) {
        return original(s)->common.get_sample_rate(&original(s)->common);
    }
    static int set_sample_rate(audio_stream* s, uint32_t rate) {
        return original(s)->common.set_sample_rate ? original(s)->common.set_sample_rate(&original(s)->common, rate) : -ENOSYS;
    }
    static size_t get_buffer_size(const audio_stream* s) {
        return original(s)->common.get_buffer_size(&original(s)->common);
    }
    static audio_channel_mask_t get_channels(const audio_stream* s) {
        return original(s)->common.get_channels(&original(s)->common);
    }
    static audio_format_t get_format(const audio_stream* s) {
        return original(s)->common.get_format(&original(s)->common);
    }
    static int set_format(audio_stream* s, audio_format_t format) {
        return original(s)->common.set_format ? original(s)->common.set_format(&original(s)->common, format) : -ENOSYS;
    }
    static int standby(audio_stream* s) {
        return original(s)->common.standby(&original(s)->common);
    }
    static int dump(const audio_stream* s, int fd) {
        return original(s)->common.dump ? original(s)->common.dump(&original(s)->common, fd) : -ENOSYS;
    }
    static audio_devices_t get_device(const audio_stream* s) {
        return original(s)->common.get_device ? original(s)->common.get_device(&original(s)->common) : AUDIO_DEVICE_NONE;
    }
    static int set_device(audio_stream* s, audio_devices_t device) {
        return original(s)->common.set_device ? original(s)->common.set_device(&original(s)->common, device) : -ENOSYS;
    }
    static int set_parameters(audio_stream* s, const char* pairs) {
        return original(s)->common.set_parameters(&original(s)->common, pairs);
    }
    static char* get_parameters(const audio_stream* s, const char* keys) {
        return original(s)->common.get_parameters(&original(s)->common, keys);
    }
    static int add_audio_effect(const audio_stream* s, effect_handle_t effect) {
        return original(s)->common.add_audio_effect ? original(s)->common.add_audio_effect(&original(s)->common, effect) : -ENOSYS;
    }
    static int remove_audio_effect(const audio_stream* s, effect_handle_t effect) {
        return original(s)->common.remove_audio_effect ? original(s)->common.remove_audio_effect(&original(s)->common, effect) : -ENOSYS;
    }
    static void initialize(Proxy<Stream>* p) {
        p->stream.common.get_sample_rate = get_sample_rate;
        p->stream.common.set_sample_rate = set_sample_rate;
        p->stream.common.get_buffer_size = get_buffer_size;
        p->stream.common.get_channels = get_channels;
        p->stream.common.get_format = get_format;
        p->stream.common.set_format = set_format;
        p->stream.common.standby = standby;
        p->stream.common.dump = dump;
        p->stream.common.get_device = get_device;
        p->stream.common.set_device = set_device;
        p->stream.common.set_parameters = set_parameters;
        p->stream.common.get_parameters = get_parameters;
        p->stream.common.add_audio_effect = add_audio_effect;
        p->stream.common.remove_audio_effect = remove_audio_effect;
    }
};

struct Output {
    static int set_parameters(audio_stream* common, const char* pairs) {
        audio_stream_out* s = reinterpret_cast<audio_stream_out*>(common);
        Parameters parameters{pairs};
        int route;
        const uint32_t local = AUDIO_DEVICE_OUT_SPEAKER |
                AUDIO_DEVICE_OUT_WIRED_HEADSET | AUDIO_DEVICE_OUT_WIRED_HEADPHONE;
        if (parameters.getInt(AUDIO_PARAMETER_STREAM_ROUTING, route) == 0 &&
                ((audio_devices_t)route & ~local) == 0) {
            // ANI7 out_set_parameters skips routing unless BOTH keys exist.
            // Its path table maps 0 to hifi. Stock policy uses phone_volume=230
            // outside calls; stream attenuation remains AudioFlinger's job.
            int existing;
            if (parameters.getInt("path_handler", existing) != 0)
                parameters.addInt("path_handler", 0);
            if (parameters.getInt("phone_volume", existing) != 0)
                parameters.addInt("phone_volume", 230);
        }
        return original(s)->common.set_parameters(
                &original(s)->common, parameters.toString().c_str());
    }
    static audio_stream_out* original(const audio_stream_out* s) {
        return reinterpret_cast<const Proxy<audio_stream_out>*>(s)->original;
    }
    static uint32_t get_latency(const audio_stream_out* s) {
        return original(s)->get_latency(original(s));
    }
    static int set_volume(audio_stream_out* s, float left, float right) {
        return original(s)->set_volume(original(s), left, right);
    }
    static ssize_t write(audio_stream_out* s, const void* buffer, size_t bytes) {
        return original(s)->write(original(s), buffer, bytes);
    }
    static int get_render_position(const audio_stream_out* s, uint32_t* frames) {
        return original(s)->get_render_position ? original(s)->get_render_position(original(s), frames) : -ENOSYS;
    }
    static int get_next_write_timestamp(const audio_stream_out* s, int64_t* timestamp) {
        return original(s)->get_next_write_timestamp(original(s), timestamp);
    }
    static audio_stream_out* wrap(audio_stream_out* originalStream) {
        if (!originalStream) return NULL;
        Proxy<audio_stream_out>* p = new (std::nothrow) Proxy<audio_stream_out>();
        if (!p) return NULL;
        p->original = originalStream;
        Common<audio_stream_out>::initialize(p);
        p->stream.common.set_parameters = set_parameters;
        if (originalStream->get_latency) p->stream.get_latency = get_latency;
        if (originalStream->set_volume) p->stream.set_volume = set_volume;
        if (originalStream->write) p->stream.write = write;
        p->stream.get_render_position = get_render_position;
        if (originalStream->get_next_write_timestamp) p->stream.get_next_write_timestamp = get_next_write_timestamp;
        return &p->stream;
    }
    // Caller closes this returned original with its real HAL, then owns no proxy.
    static audio_stream_out* unwrapAndDestroy(audio_stream_out* s) {
        if (!s) return NULL;
        Proxy<audio_stream_out>* p = reinterpret_cast<Proxy<audio_stream_out>*>(s);
        audio_stream_out* originalStream = p->original;
        delete p;
        return originalStream;
    }
};

struct Input {
    static audio_stream_in* original(const audio_stream_in* s) {
        return reinterpret_cast<const Proxy<audio_stream_in>*>(s)->original;
    }
    static int set_gain(audio_stream_in* s, float gain) {
        return original(s)->set_gain(original(s), gain);
    }
    static int setActive(audio_stream_in* s, bool active) {
        Proxy<audio_stream_in>* p = reinterpret_cast<Proxy<audio_stream_in>*>(s);
        Parameters parameters;
        parameters.addInt(AUDIO_PARAMETER_STREAM_ROUTING, (int)p->routing);
        parameters.addInt("STREAM_IN_ACTIVE", active ? 1 : 0);
        const int result = original(s)->common.set_parameters(
                &original(s)->common, parameters.toString().c_str());
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
        Parameters parameters{pairs};
        int routing;
        const bool hasRoute = parameters.getInt(
                AUDIO_PARAMETER_STREAM_ROUTING, routing) == 0;
        if (hasRoute && routing == 0 && p->active) {
            const int result = setActive(s, false);
            if (result != 0) return result;
        }
        if (hasRoute && p->active) parameters.addInt("STREAM_IN_ACTIVE", 1);
        const int result = original(s)->common.set_parameters(
                &original(s)->common, parameters.toString().c_str());
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
    }
    static uint32_t get_input_frames_lost(audio_stream_in* s) {
        return original(s)->get_input_frames_lost ? original(s)->get_input_frames_lost(original(s)) : 0;
    }
    static audio_stream_in* wrap(audio_stream_in* originalStream, audio_devices_t initialRoute) {
        if (!originalStream) return NULL;
        Proxy<audio_stream_in>* p = new (std::nothrow) Proxy<audio_stream_in>();
        if (!p) return NULL;
        p->original = originalStream;
        p->routing = initialRoute;
        Common<audio_stream_in>::initialize(p);
        p->stream.common.standby = standby;
        p->stream.common.set_parameters = set_parameters;
        if (originalStream->set_gain) p->stream.set_gain = set_gain;
        if (originalStream->read) p->stream.read = read;
        p->stream.get_input_frames_lost = get_input_frames_lost;
        return &p->stream;
    }
    // Caller closes this returned original with its real HAL, then owns no proxy.
    static audio_stream_in* unwrapAndDestroy(audio_stream_in* s) {
        if (!s) return NULL;
        Proxy<audio_stream_in>* p = reinterpret_cast<Proxy<audio_stream_in>*>(s);
        audio_stream_in* originalStream = p->original;
        delete p;
        return originalStream;
    }
};

static_assert(offsetof(Proxy<audio_stream_out>, stream) == 0, "output prefix");
static_assert(offsetof(Proxy<audio_stream_in>, stream) == 0, "input prefix");
#if defined(__arm__) && !defined(__LP64__)
static_assert(offsetof(audio_stream_out, get_next_write_timestamp) == 72, "ANI7 output prefix");
static_assert(offsetof(audio_stream_in, get_input_frames_lost) == 64, "ANI7 input prefix");
#endif
} // namespace t110_audio_compat
} // namespace android
#endif // T110_MRVL_LEGACY
#endif // T110_AUDIO_STREAM_COMPAT_H
