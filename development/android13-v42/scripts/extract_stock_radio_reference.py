"""Extract the stock radio module and firmware reference from Samsung's ramdisk."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import stat

project = Path(__file__).resolve().parents[1]
data = (project / "firmware/extracted/boot/ramdisk.cpio").read_bytes()
output = project / "evidence/stock-radio-reference"
output.mkdir(exist_ok=True)
offset = 0
records = {}
while offset < len(data):
    header = data[offset:offset + 110]
    assert header[:6] in (b"070701", b"070702")
    fields = [int(header[i:i + 8], 16) for i in range(6, 110, 8)]
    mode, size, namesize = fields[1], fields[6], fields[11]
    offset += 110
    assert namesize and data[offset + namesize - 1] == 0
    name = data[offset:offset + namesize - 1].decode()
    offset = (offset + namesize + 3) & ~3
    content = data[offset:offset + size]
    assert len(content) == size
    offset = (offset + size + 3) & ~3
    if name == "TRAILER!!!":
        break
    path = PurePosixPath(name)
    if not stat.S_ISREG(mode):
        continue
    if path.name not in {"mlan.ko", "sd8xxx.ko", "sd8777_uapsta.bin", "WlanCalData_ext.conf",
                         "cal_data.conf", "init.pxa988.rc", "init.rc", "ueventd.pxa988.rc"}:
        continue
    assert not path.is_absolute() and ".." not in path.parts
    destination = output.joinpath(*path.parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    records[name] = {"bytes": size, "sha256": hashlib.sha256(content).hexdigest()}

assert {"lib/modules/mlan.ko", "lib/modules/sd8xxx.ko"} <= records.keys()
(output / "inventory.json").write_text(json.dumps(records, indent=2) + "\n")
print(json.dumps(records, indent=2))
