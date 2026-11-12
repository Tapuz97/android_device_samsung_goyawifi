"""Check a completed raw or Android sparse ext4 system image without mounting it."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

SYSTEM_BYTES = 3_115_008 * 512  # SM-T110 mmcblk0p15, confirmed on the tablet.
SPARSE_MAGIC = 0xED26FF3A


def inspect_ext4(raw):
    with raw.open('rb') as stream:
        stream.seek(1024)
        superblock = stream.read(1024)
    if len(superblock) != 1024 or struct.unpack_from('<H', superblock, 56)[0] != 0xEF53:
        raise ValueError('No ext4 superblock at offset 1024')
    blocks = struct.unpack_from('<I', superblock, 4)[0]
    block_exponent = struct.unpack_from('<I', superblock, 24)[0]
    if block_exponent > 6:
        raise ValueError('Invalid ext4 block size')
    compat, incompat, ro_compat = struct.unpack_from('<III', superblock, 92)
    if incompat & 0x80:  # EXT4_FEATURE_INCOMPAT_64BIT
        blocks |= struct.unpack_from('<I', superblock, 336)[0] << 32
    fs_bytes = blocks * (1024 << block_exponent)
    if not fs_bytes or fs_bytes > raw.stat().st_size:
        raise ValueError('The ext4 filesystem extends past the image')
    fsck = subprocess.run(['e2fsck', '-f', '-n', str(raw)], capture_output=True, text=True, timeout=300)
    return {'ext4_bytes': fs_bytes, 'ext4_features': {
                'compat': hex(compat), 'incompat': hex(incompat), 'ro_compat': hex(ro_compat)},
            'fsck_exit': fsck.returncode, 'fsck_output': fsck.stdout + fsck.stderr}


def verify(image):
    report = {'file': str(image), 'partition': 'mmcblk0p15', 'partition_bytes': SYSTEM_BYTES,
              'file_bytes': image.stat().st_size}
    with image.open('rb') as stream:
        header = stream.read(28)
        if len(header) != 28:
            raise ValueError('Image header is truncated')
        magic, major, _, header_size, chunk_header_size, block_size, blocks, chunks, _ = struct.unpack('<I4H4I', header)
        sparse = magic == SPARSE_MAGIC
        if sparse and (major != 1 or header_size < 28 or chunk_header_size < 12 or
                       block_size < 4 or block_size % 4 or not blocks or not chunks):
            raise ValueError('Invalid Android sparse header')
        stream.seek(0)
        report['sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
    expanded = block_size * blocks if sparse else report['file_bytes']
    report.update(format='android_sparse' if sparse else 'raw', expanded_bytes=expanded,
                  partition_headroom_bytes=SYSTEM_BYTES-expanded, fits=expanded <= SYSTEM_BYTES)
    if not report['fits']:
        return report
    if sparse:
        with tempfile.TemporaryDirectory(prefix='t110-system-verify-', dir=image.parent) as temporary:
            raw = Path(temporary)/'system.raw.img'
            subprocess.run(['simg2img', str(image), str(raw)], check=True, timeout=300)
            if raw.stat().st_size != expanded:
                raise ValueError('Expanded size disagrees with the sparse header')
            report.update(inspect_ext4(raw))
    else:
        report.update(inspect_ext4(image))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    result = verify(args.image.resolve(strict=True))
    result['status'] = ('TOO_LARGE' if not result['fits'] else
                        'FIT_AND_EXT4_VERIFIED' if result['fsck_exit'] == 0 else 'EXT4_CHECK_FAILED')
    args.report.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'fsck_output'}, indent=2))
    raise SystemExit(0 if result['status'] == 'FIT_AND_EXT4_VERIFIED' else 2)
