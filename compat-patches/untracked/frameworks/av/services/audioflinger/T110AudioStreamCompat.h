/*
 * Copyright 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef T110_AUDIO_STREAM_COMPAT_H
#define T110_AUDIO_STREAM_COMPAT_H
#if defined(T110_MRVL_LEGACY)
#include <hardware/audio.h>
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

template<typename Stream> struct Common {
    static Stream* original(const audio_stream* s) {
        return reinterpret_cast<const Proxy<Stream>*>(s)->original;
    }
    static uint32_t get_sample_rate(const audio_stream* s) {
        return original(s)->common.get_sample_rate(&original(s)->common);
    }
    static int set_sample_rate(audio_stream* s, uint32_t rate) {
        return original(s)->common.set_sample_rate(&original(s)->common, rate);
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
        return original(s)->common.set_format(&original(s)->common, format);
    }
    static int standby(audio_stream* s) {
        return original(s)->common.standby(&original(s)->common);
    }
    static int dump(const audio_stream* s, int fd) {
        return original(s)->common.dump(&original(s)->common, fd);
    }
    static audio_devices_t get_device(const audio_stream* s) {
        return original(s)->common.get_device(&original(s)->common);
    }
    static int set_device(audio_stream* s, audio_devices_t device) {
        return original(s)->common.set_device(&original(s)->common, device);
    }
    static int set_parameters(audio_stream* s, const char* pairs) {
        return original(s)->common.set_parameters(&original(s)->common, pairs);
    }
    static char* get_parameters(const audio_stream* s, const char* keys) {
        return original(s)->common.get_parameters(&original(s)->common, keys);
    }
    static int add_audio_effect(const audio_stream* s, effect_handle_t effect) {
        return original(s)->common.add_audio_effect(&original(s)->common, effect);
    }
    static int remove_audio_effect(const audio_stream* s, effect_handle_t effect) {
        return original(s)->common.remove_audio_effect(&original(s)->common, effect);
    }
    static void initialize(Proxy<Stream>* p) {
        if (p->original->common.get_sample_rate) p->stream.common.get_sample_rate = get_sample_rate;
        if (p->original->common.set_sample_rate) p->stream.common.set_sample_rate = set_sample_rate;
        if (p->original->common.get_buffer_size) p->stream.common.get_buffer_size = get_buffer_size;
        if (p->original->common.get_channels) p->stream.common.get_channels = get_channels;
        if (p->original->common.get_format) p->stream.common.get_format = get_format;
        if (p->original->common.set_format) p->stream.common.set_format = set_format;
        if (p->original->common.standby) p->stream.common.standby = standby;
        if (p->original->common.dump) p->stream.common.dump = dump;
        if (p->original->common.get_device) p->stream.common.get_device = get_device;
        if (p->original->common.set_device) p->stream.common.set_device = set_device;
        if (p->original->common.set_parameters) p->stream.common.set_parameters = set_parameters;
        if (p->original->common.get_parameters) p->stream.common.get_parameters = get_parameters;
        if (p->original->common.add_audio_effect) p->stream.common.add_audio_effect = add_audio_effect;
        if (p->original->common.remove_audio_effect) p->stream.common.remove_audio_effect = remove_audio_effect;
    }
};

struct Output {
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
        return original(s)->get_render_position(original(s), frames);
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
        if (originalStream->get_latency) p->stream.get_latency = get_latency;
        if (originalStream->set_volume) p->stream.set_volume = set_volume;
        if (originalStream->write) p->stream.write = write;
        if (originalStream->get_render_position) p->stream.get_render_position = get_render_position;
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
    static ssize_t read(audio_stream_in* s, void* buffer, size_t bytes) {
        return original(s)->read(original(s), buffer, bytes);
    }
    static uint32_t get_input_frames_lost(audio_stream_in* s) {
        return original(s)->get_input_frames_lost(original(s));
    }
    static audio_stream_in* wrap(audio_stream_in* originalStream) {
        if (!originalStream) return NULL;
        Proxy<audio_stream_in>* p = new (std::nothrow) Proxy<audio_stream_in>();
        if (!p) return NULL;
        p->original = originalStream;
        Common<audio_stream_in>::initialize(p);
        if (originalStream->set_gain) p->stream.set_gain = set_gain;
        if (originalStream->read) p->stream.read = read;
        if (originalStream->get_input_frames_lost) p->stream.get_input_frames_lost = get_input_frames_lost;
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
