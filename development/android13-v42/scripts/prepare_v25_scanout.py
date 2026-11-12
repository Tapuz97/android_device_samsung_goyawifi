"""Stage the rotated image in cached RAM, then copy rows to device memory."""
from pathlib import Path
import difflib
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
t=Path('/root/t110-build/lineage20')
fn='graphics/composer/2.1/default/T110Framebuffer.cpp'
path=t/'hardware/interfaces'/fn;old=path.read_text();new=old
new=new.replace('#include <mutex>','#include <mutex>\n#include <vector>\n#include <chrono>')
new=new.replace('    uint64_t frames = 0;','''    // The fbdev mapping is uncached device memory. Rotate in cached RAM and
    // stream complete rows to fbdev, instead of issuing one small store per pixel.
    std::vector<uint8_t> rotated;
    uint64_t copyNanoseconds = 0;
    uint64_t postNanoseconds = 0;
    uint64_t frames = 0;''')
new=new.replace('    // Exact stock gralloc ABI,', '''    const auto postStart = std::chrono::steady_clock::now();
    // Exact stock gralloc ABI,''')
anchor='''    bool copied = t110::copyPortraitFrame(d->pixels, d->fixed.smem_len, d->fixed, d->mode,
                                  page, source, words[7], words[16]);'''
assert new.count(anchor)==1
new=new.replace(anchor,'''    const auto copyStart = std::chrono::steady_clock::now();
    bool copied = t110::copyPortraitFrame(d->rotated.data(), d->rotated.size(),
                                  d->fixed, d->mode, 0, source, words[7], words[16]);
    if (copied) {
        auto* destination = static_cast<uint8_t*>(d->pixels) +
                size_t(page) * d->fixed.line_length;
        for (uint32_t y = 0; y < d->mode.yres; ++y) {
            memcpy(destination + size_t(y) * d->fixed.line_length,
                   d->rotated.data() + size_t(y) * d->fixed.line_length,
                   size_t(d->mode.xres) * 4);
        }
    }
    d->copyNanoseconds += std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now() - copyStart).count();''')
new=new.replace('    ++d->frames;','''    ++d->frames;
    d->postNanoseconds += std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now() - postStart).count();''')
new=new.replace('error=%d blanked=%d\\n",','error=%d blanked=%d copy_ns=%llu post_ns=%llu\\n",')
new=new.replace('                          static_cast<int>(d->blanked));','''                          static_cast<int>(d->blanked),
                          static_cast<unsigned long long>(d->copyNanoseconds),
                          static_cast<unsigned long long>(d->postNanoseconds));''')
new=new.replace('    d->pixels = mmap(','''    d->rotated.resize(size_t(d->fixed.line_length) * d->mode.yres);
    d->pixels = mmap(''')
assert old!=new
(p/'patches/0064-composer-t110-cached-scanout-staging.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+fn,tofile='b/'+fn)),encoding='utf-8')
path.write_text(new,encoding='utf-8')
fn='libs/renderengine/gl/T110EglWindow.cpp';path=t/'frameworks/native'/fn;old=path.read_text()
anchor='''            self->mBuffers[slot] = sp<GraphicBuffer>::make(
                    target->getWidth(), target->getHeight(), target->getPixelFormat(), 1,
                    target->getUsage(), "T110 EGL swap spare");'''
assert old.count(anchor)==1
new=old.replace(anchor,'''            // The window is one-shot, but the driver's spare allocation can be
            // retained across frames. Reuse only after EGL and the previous
            // window have released every reference. Never share a busy spare.
            static thread_local std::array<sp<GraphicBuffer>, 2> spareCache;
            for (const auto& spare : spareCache) {
                if (spare && spare->getStrongCount() == 1 &&
                    spare->getWidth() == target->getWidth() &&
                    spare->getHeight() == target->getHeight() &&
                    spare->getPixelFormat() == target->getPixelFormat() &&
                    spare->getUsage() == target->getUsage()) {
                    self->mBuffers[slot] = spare;
                    break;
                }
            }
            if (!self->mBuffers[slot]) {
                self->mBuffers[slot] = sp<GraphicBuffer>::make(
                        target->getWidth(), target->getHeight(), target->getPixelFormat(), 1,
                        target->getUsage(), "T110 EGL swap spare");
                if (self->mBuffers[slot]->initCheck() == NO_ERROR) {
                    for (auto& spare : spareCache) {
                        if (!spare || spare->getStrongCount() == 1) {
                            spare = self->mBuffers[slot];
                            break;
                        }
                    }
                }
            }''')
(p/'patches/0065-renderengine-t110-reuse-idle-swap-spares.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+fn,tofile='b/'+fn)),encoding='utf-8');path.write_text(new,encoding='utf-8')
f=p/'scripts/build_system_image.sh';s=f.read_text();anchor="'packages/apps/LineageParts:0063-lineageparts-t110-navigation-mode-switch.patch'; do"
assert s.count(anchor)==1
s=s.replace(anchor,"'packages/apps/LineageParts:0063-lineageparts-t110-navigation-mode-switch.patch' 'hardware/interfaces:0064-composer-t110-cached-scanout-staging.patch' 'frameworks/native:0065-renderengine-t110-reuse-idle-swap-spares.patch'; do")
f.write_text(s,encoding='utf-8')
print('SCANOUT_AND_SPARE_REUSE_PREPARED')
