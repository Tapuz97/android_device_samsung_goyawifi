from pathlib import Path
import re,hashlib,json
root=Path('/root/t110-android13-audit')
dest=root/'device/development/android13-audit-20261114/implementation/audio'
dest.mkdir(parents=True,exist_ok=True)
source=Path('/root/t110-lineage14/android/device/samsung/goyawifi/compat-patches/untracked/frameworks/av/services/audioflinger/T110AudioStreamCompat.h')
s=source.read_text().replace('#if defined(T110_MRVL_LEGACY)','#if defined(T110_MRVL_LEGACY)')
s=s.replace('#include <media/AudioParameter.h>','#include "Parameters.h"')
s=s.replace('AudioParameter','Parameters').replace('String8(pairs)','pairs')
s=s.replace('NO_ERROR','0').replace('const audio_devices_t local =','const uint32_t local =')
s=re.sub(r'String8\(("[^"]+"|[A-Z_]+)\)',r'\1',s)
s=s.replace('.toString().string()', '.toString().c_str()')
# HIDL directly invokes several common callbacks. Fill safe unsupported stubs
# rather than leaving null pointers for fields absent from the old HAL.
for name,expr in {
'set_sample_rate':'original(s)->common.set_sample_rate ? original(s)->common.set_sample_rate(&original(s)->common, rate) : -ENOSYS',
'set_format':'original(s)->common.set_format ? original(s)->common.set_format(&original(s)->common, format) : -ENOSYS',
'dump':'original(s)->common.dump ? original(s)->common.dump(&original(s)->common, fd) : -ENOSYS',
'get_device':'original(s)->common.get_device ? original(s)->common.get_device(&original(s)->common) : AUDIO_DEVICE_NONE',
'set_device':'original(s)->common.set_device ? original(s)->common.set_device(&original(s)->common, device) : -ENOSYS',
'add_audio_effect':'original(s)->common.add_audio_effect ? original(s)->common.add_audio_effect(&original(s)->common, effect) : -ENOSYS',
'remove_audio_effect':'original(s)->common.remove_audio_effect ? original(s)->common.remove_audio_effect(&original(s)->common, effect) : -ENOSYS',
}.items():
 pattern=r'(static [^\n]+ '+name+r'\([^\{]+\{\n)        return [^;]+;'
 s,n=re.subn(pattern,lambda m:m[1]+'        return '+expr+';',s,count=1)
 assert n==1,name
s=re.sub(r'if \(p->original->common\.\w+\) (p->stream.common\.\w+ = \w+;)',r'\1',s)
s=s.replace('return original(s)->get_render_position(original(s), frames);','return original(s)->get_render_position ? original(s)->get_render_position(original(s), frames) : -ENOSYS;')
s=s.replace('if (originalStream->get_render_position) p->stream.get_render_position = get_render_position;','p->stream.get_render_position = get_render_position;')
s=s.replace('return original(s)->get_input_frames_lost(original(s));','return original(s)->get_input_frames_lost ? original(s)->get_input_frames_lost(original(s)) : 0;')
s=s.replace('if (originalStream->get_input_frames_lost) p->stream.get_input_frames_lost = get_input_frames_lost;','p->stream.get_input_frames_lost = get_input_frames_lost;')
s=s.replace('static audio_stream_in* wrap(audio_stream_in* originalStream) {','static audio_stream_in* wrap(audio_stream_in* originalStream, audio_devices_t initialRoute) {')
anchor='''        p->original = originalStream;
        Common<audio_stream_in>::initialize(p);'''
assert anchor in s
s=s.replace(anchor,'''        p->original = originalStream;
        p->routing = initialRoute;
        Common<audio_stream_in>::initialize(p);''')
(dest/'StreamCompat.h').write_text(s)
(dest/'provenance.json').write_text(json.dumps(dict(nougat_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),changes=['Standalone parameter parser; no libmedia/String8 ABI dependency','Input route initialized from open_input_stream device argument','Modern full-size zero-initialized stream structures retain the tested ANI7 prefixes']),indent=2)+'\n')
print(dest)
