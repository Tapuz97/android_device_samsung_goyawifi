"""Verify a transport archive, then extract its two payload files to a NEW folder."""
import argparse
from pathlib import Path
import shutil
import zipfile
from verify_modern_package import verify

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    verify(args.archive)
    args.destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(args.archive) as archive:
        for name in ('system.raw.img.gz', 'boot.img', 'manifest.json'):
            with archive.open(name) as source, (args.destination / name).open('wb') as target:
                shutil.copyfileobj(source, target)
    print('Verified payload extracted; follow docs/INSTALLATION.md. No tablet was touched.')
