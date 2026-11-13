"""Retain the preview surface until the synchronous legacy HAL detach completes."""
from pathlib import Path
p=Path('/root/t110-lineage14/android/frameworks/av/services/camera/libcameraservice/device1/CameraHardwareInterface.h')
s=p.read_text()
old='''        if (mDevice->ops->set_preview_window) {
            mPreviewWindow = buf;'''
new='''        if (mDevice->ops->set_preview_window) {
#ifdef T110_MRVL_LEGACY
            if (buf == nullptr) {
                // Marvell stops its display worker inside set_preview_window.
                // Clearing first lets the worker call dequeue on a null window.
                const status_t result = mDevice->ops->set_preview_window(mDevice, nullptr);
                if (result == OK) mPreviewWindow.clear();
                return result;
            }
#endif
            mPreviewWindow = buf;'''
if new not in s:
    assert s.count(old)==1
    s=s.replace(old,new)
p.write_text(s)
print('Retain preview window through Marvell HAL detach.')
