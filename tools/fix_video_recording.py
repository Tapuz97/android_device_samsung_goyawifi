"""Restore the camera's I420 alias and register existing Nougat codecs."""
from pathlib import Path
base=Path('/root/t110-lineage14/android')
p=base/'frameworks/av/media/libstagefright/CameraSource.cpp'
s=p.read_text()
anchor='    if (!strcmp(colorFormat, CameraParameters::PIXEL_FORMAT_YUV420P)) {'
addition='''#ifdef T110_MRVL_LEGACY
    // The stock Marvell HAL names planar Y/U/V 4:2:0 explicitly as I420.
    // It is a pixel buffer, not an opaque metadata/native-handle format.
    if (!strcmp(colorFormat, "yuv420p-i420")) {
        return OMX_COLOR_FormatYUV420Planar;
    }
#endif

'''
if addition not in s:
    assert s.count(anchor)==1
    p.write_text(s.replace(anchor,addition+anchor))
d=base/'device/samsung/goyawifi'
p=base/'frameworks/av/services/camera/libcameraservice/device1/CameraHardwareInterface.h'
s=p.read_text()
old='''        if (mDevice->ops->store_meta_data_in_buffers)
            return mDevice->ops->store_meta_data_in_buffers(mDevice, enable);
        return enable ? INVALID_OPERATION: OK;'''
new='''        if (mDevice->ops->store_meta_data_in_buffers) {
            const status_t result = mDevice->ops->store_meta_data_in_buffers(mDevice, enable);
#ifdef T110_MRVL_LEGACY
            // ANI7's callback is a six-byte unconditional return -1 stub.
            // Its I420 recording mode already returns actual YUV data. Only
            // tolerate disabling metadata for that known mode, never enabling it.
            if (!enable && result == -1) {
                const CameraParameters parameters = getParameters();
                const char* format = parameters.get(CameraParameters::KEY_VIDEO_FRAME_FORMAT);
                if (format && !strcmp(format, "yuv420p-i420")) return OK;
            }
#endif
            return result;
        }
        return enable ? INVALID_OPERATION: OK;'''
if new not in s:
    assert s.count(old)==1
    p.write_text(s.replace(old,new))
(d/'configs/media_codecs.xml').write_text('''<?xml version="1.0" encoding="utf-8"?>
<!-- Register the codecs actually built from this Nougat source tree.
     Legacy hardware OMX must be qualified before it is advertised here. -->
<MediaCodecs>
    <Include href="media_codecs_google_audio.xml" />
    <Include href="media_codecs_google_video.xml" />
    <Include href="media_codecs_google_telephony.xml" />
</MediaCodecs>
''')
p=d/'device.mk'; s=p.read_text()
block='''
# Register standard codecs already present in the product; no unverified vendor OMX.
PRODUCT_COPY_FILES += $(LOCAL_PATH)/configs/media_codecs.xml:system/etc/media_codecs.xml
PRODUCT_COPY_FILES += frameworks/av/media/libstagefright/data/media_codecs_google_audio.xml:system/etc/media_codecs_google_audio.xml
PRODUCT_COPY_FILES += frameworks/av/media/libstagefright/data/media_codecs_google_video.xml:system/etc/media_codecs_google_video.xml
PRODUCT_COPY_FILES += frameworks/av/media/libstagefright/data/media_codecs_google_telephony.xml:system/etc/media_codecs_google_telephony.xml
'''
if block not in s:p.write_text(s+block)
p=d/'configs/audio_policy.conf'; s=p.read_text()
old='''      primary {
        sampling_rates 44100|48000
        channel_masks AUDIO_CHANNEL_OUT_STEREO'''
new='''      primary {
        sampling_rates 44100
        channel_masks AUDIO_CHANNEL_OUT_STEREO'''
assert old in s or new in s
p.write_text(s.replace(old,new))
p=d/'rootdir/init.mrvl.rc'; s=p.read_text()
block='''
# Stock ANI7 selects AP-master audio clocks before the audio HAL starts.
# Nougat runs the HAL in audioserver, which is a member of the audio group.
on post-fs-data
    chown system audio /proc/driver/ssp_master
    chmod 0660 /proc/driver/ssp_master
    chown system audio /proc/driver/gssp_master
    chmod 0660 /proc/driver/gssp_master
    setprop persist.audio.apmaster 1
    setprop persist.audio.gsspmaster 1
    setprop persist.audio.codecmaster 0
'''
if block not in s:p.write_text(s+block)
print('Restored I420 video format alias and standard codec registration.')
