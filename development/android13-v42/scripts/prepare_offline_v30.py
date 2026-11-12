"""Keep Android in natural portrait; apply fixed panel rotation at scanout."""
from pathlib import Path
import difflib,json,subprocess
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
t=Path('/root/t110-build/lineage20');e=p/'evidence/offline-v30';e.mkdir(exist_ok=True)
h=t/'hardware/interfaces'
fb=h/'graphics/composer/2.1/default/T110Framebuffer.cpp'
scan=h/'graphics/composer/2.1/default/T110Scanout.h'
def replace(file,old,new):
    text=file.read_text();assert text.count(old)==1,(str(file),old)
    backup=e/(file.name+'.before');assert not backup.exists()
    backup.write_text(text);file.write_text(text.replace(old,new))
text=scan.read_text();(e/'T110Scanout.h.before').write_text(text)
extra='''// Android renders natural portrait. The PXA panel is wired 270 degrees
// from it: logical (x,y) maps to native (y,599-x). Rotate once here,
// after EGL has resolved the complete frame; keep fbdev in its native mode.
constexpr uint32_t kLogicalWidth = 600;
constexpr uint32_t kLogicalHeight = 1024;
inline bool copyPortraitFrame(void* destination, size_t destinationBytes,
                              const fb_fix_screeninfo& f, const fb_var_screeninfo& v,
                              uint32_t pageY, const void* source, size_t sourceBytes,
                              uint32_t sourceStridePixels) {
    if (!destination || !source || !validFramebuffer(f, v) ||
        pageY % v.yres || uint64_t(pageY) + v.yres > v.yres_virtual ||
        sourceStridePixels < kLogicalWidth ||
        uint64_t(sourceStridePixels) * 4 * kLogicalHeight > sourceBytes ||
        uint64_t(f.line_length) * (uint64_t(pageY) + v.yres) > destinationBytes) return false;
    auto* dst = static_cast<uint8_t*>(destination) + size_t(pageY) * f.line_length;
    const auto* src = static_cast<const uint8_t*>(source);
    const uint32_t alpha = v.transp.length ? (255u << v.transp.offset) : 0;
    // Small tiles keep both transposed source rows and destination rows hot.
    constexpr uint32_t tile = 32;
    for (uint32_t by = 0; by < v.yres; by += tile) {
        const uint32_t ey = by + tile < v.yres ? by + tile : v.yres;
        for (uint32_t bx = 0; bx < v.xres; bx += tile) {
            const uint32_t ex = bx + tile < v.xres ? bx + tile : v.xres;
            for (uint32_t y = by; y < ey; ++y) {
                auto* row = dst + size_t(y) * f.line_length;
                for (uint32_t x = bx; x < ex; ++x) {
                    const auto* pixel = src + (size_t(x) * sourceStridePixels + kLogicalWidth - 1 - y) * 4;
                    const uint32_t packed = (uint32_t(pixel[0]) << v.red.offset) |
                                            (uint32_t(pixel[1]) << v.green.offset) |
                                            (uint32_t(pixel[2]) << v.blue.offset) | alpha;
                    memcpy(row + size_t(x) * 4, &packed, sizeof(packed));
                }
            }
        }
    }
    return true;
}
'''
assert 'copyPortraitFrame' not in text
scan.write_text(text.replace('} // namespace t110',extra+'} // namespace t110'))
text=fb.read_text();(e/'T110Framebuffer.cpp.before').write_text(text)
text=text.replace('words[13] < d->mode.xres || words[14] < d->mode.yres ||','words[13] != t110::kLogicalWidth || words[14] != t110::kLogicalHeight ||')
text=text.replace('words[16] < d->mode.xres || words[17] < d->mode.yres ||','words[16] < t110::kLogicalWidth || words[17] < t110::kLogicalHeight ||')
text=text.replace('uint64_t(words[16]) * 4 * d->mode.yres > words[7]','uint64_t(words[16]) * 4 * t110::kLogicalHeight > words[7]')
text=text.replace('0, 0, d->mode.xres, d->mode.yres, &source','0, 0, t110::kLogicalWidth, t110::kLogicalHeight, &source')
text=text.replace('t110::copyFrame(', 't110::copyPortraitFrame(')
text=text.replace('d->fb.width) = d->mode.xres','d->fb.width) = t110::kLogicalWidth').replace('d->fb.height) = d->mode.yres','d->fb.height) = t110::kLogicalHeight')
text=text.replace('d->fb.stride) = d->fixed.line_length / 4','d->fb.stride) = t110::kLogicalWidth')
text=text.replace('T110 direct framebuffer presenter ready; PXA ION read synchronization enabled','T110 natural portrait presenter ready; final panel rotation=270; PXA ION sync enabled')
assert 't110::copyPortraitFrame(' in text and 'words[13] != t110::kLogicalWidth' in text
fb.write_text(text)
for file in [fb,scan]: (p/'work'/file.name).write_text(file.read_text())
product=p/'work/device/samsung/t110_bringup/t110_system.mk'
replace(product,'# Stock T110 build.prop specifies hwrotation=270. Let SurfaceFlinger expose\n# the natural 600x1024 portrait display and undo panel rotation for input.\nPRODUCT_SYSTEM_PROPERTIES += ro.surface_flinger.primary_display_orientation=ORIENTATION_270',
        '# The framebuffer adapter exposes natural 600x1024 and applies the stock\n# fixed panel rotation at scanout. Do not rotate a second time in SurfaceFlinger.\nPRODUCT_SYSTEM_PROPERTIES += ro.surface_flinger.primary_display_orientation=ORIENTATION_0')
# Supersede the existing cumulative adapter patch, retaining its power fix.
paths=['graphics/composer/2.1/default/Android.bp','graphics/composer/2.1/default/service.cpp',
       'graphics/composer/2.1/default/T110Framebuffer.cpp','graphics/composer/2.1/default/T110Framebuffer.h',
       'graphics/composer/2.1/default/T110Scanout.h',
       'graphics/composer/2.1/utils/hwc2onfbadapter/HWC2OnFbAdapter.cpp',
       'graphics/composer/2.1/utils/hwc2onfbadapter/include/hwc2onfbadapter/HWC2OnFbAdapter.h']
patch=''
for name in paths:
    r=subprocess.run(['git','show','HEAD:'+name],cwd=h,capture_output=True,text=True)
    before=r.stdout if r.returncode==0 else ''
    after=(h/name).read_text()
    if before==after:continue
    patch+=f'diff --git a/{name} b/{name}\n'
    if not before:patch+='new file mode 100644\n'
    patch+=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name if before else '/dev/null',tofile='b/'+name))
name='0055-composer-t110-natural-portrait-scanout.patch'
(p/'patches'/name).write_text(patch)
subprocess.run(['git','apply','--reverse','--check',str(p/'patches'/name)],cwd=h,check=True)
script=p/'scripts/build_system_image.sh'
replace(script,'0054-composer-t110-scanout-and-display-power.patch',name)
print('V30_PORTRAIT_ADAPTER_PREPARED')
