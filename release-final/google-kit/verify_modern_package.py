"""Verify a release transport ZIP without extracting it or touching a tablet."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import zipfile

def stream_hash(source):
    size = 0
    h = hashlib.sha256()
    while chunk := source.read(1024 * 1024):
        size += len(chunk)
        h.update(chunk)
    return size, h.hexdigest()

def verify(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), "Duplicate ZIP member"
        assert all(not n.startswith(("/", "\\")) and ".." not in Path(n).parts for n in names)
        assert archive.testzip() is None, "ZIP CRC check failed"
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["modernized_ui"] is True
        assert manifest["model"] == "SM-T110" and manifest["codename"] == "goyawifi"
        assert manifest["android_sdk"] == 25 and manifest["architecture"] == "arm"
        assert manifest["container_format"] == "computer_transport_not_recovery_update"
        assert "META-INF/com/google/android/update-binary" not in names
        for name, entry in manifest["files"].items():
            with archive.open(name) as source:
                assert stream_hash(source) == (entry["bytes"], entry["sha256"]), name
        with archive.open("system.raw.img.gz") as source:
            with gzip.GzipFile(fileobj=source) as raw:
                size, digest = stream_hash(raw)
        assert size == 1594884096
        assert digest == manifest["system_raw_sha256"], "Decompressed ext4 hash mismatch"
        assert manifest["files"]["boot.img"]["bytes"] == 16777216
        assert manifest["files"]["boot.img"]["sha256"] == (
            "93aa73c2cd75efee0441513967a878eb9b92161109d326febc26a61a48b2b0f2")
        assert archive.read("boot.img")[:8] == b"ANDROID!"
        assert not any("PRIVATE" in n or "userdata" in n or "token" in n.lower() for n in names)
        print(json.dumps({"status": "PASS_ZIP_GZIP_RAW_BOOT_HASHES", "edition": manifest["edition"],
                          "modernized_ui": True, "raw_sha256": digest}))
        return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_file", type=Path)
    verify(parser.parse_args().zip_file)
