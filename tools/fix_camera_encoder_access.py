"""Give the split Nougat camera service access to its legacy JPEG encoder."""
from pathlib import Path
p = Path('/root/t110-lineage14/android/device/samsung/goyawifi/rootdir/ueventd.mrvl.rc')
s = p.read_text()
old = '/dev/uio0 0660 media media'
new = '/dev/uio0 0660 media camera'
assert old in s or new in s
p.write_text(s.replace(old, new))
print('Coda7542: preserve media owner and restrict group access to camera.')
