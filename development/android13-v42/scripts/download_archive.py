"""Download and verify the archived matching AP build (OJV regional package)."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import threading
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
NAME = "SM-T110_T110XXUANI7_T110OJVANI1.zip"
URL = "https://archive.org/download/fwatlas-samsung-sm-t110-t110xxuani7/" + NAME
SIZE = 929009316
CHUNK = 4 * 1024 * 1024

def main():
    folder = ROOT / "firmware"
    folder.mkdir(exist_ok=True)
    target = folder / NAME
    if target.exists():
        raise SystemExit("Target already exists; verify it before replacing.")
    temp = folder / (NAME + ".range.part")
    lock = threading.Lock()
    with temp.open("w+b") as output:
        output.truncate(SIZE)
        def fetch(start):
            end = min(start + CHUNK, SIZE) - 1
            for attempt in range(3):
                try:
                    req = urllib.request.Request(URL, headers={"Range": f"bytes={start}-{end}"})
                    with urllib.request.urlopen(req, timeout=45) as response:
                        if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{SIZE}":
                            raise RuntimeError("Server did not honor requested byte range")
                        data = response.read()
                    if len(data) != end - start + 1:
                        raise RuntimeError("Incomplete byte range")
                    with lock:
                        output.seek(start)
                        output.write(data)
                    return len(data)
                except Exception:
                    if attempt == 2:
                        raise
        done = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(fetch, offset) for offset in range(0, SIZE, CHUNK)]
            for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
                done += future.result()
                if index % 25 == 0:
                    print(f"Downloaded {done // (1024*1024)} MiB / {SIZE // (1024*1024)} MiB", flush=True)
    md5 = hashlib.file_digest(temp.open("rb"), "md5").hexdigest()
    sha256 = hashlib.file_digest(temp.open("rb"), "sha256").hexdigest()
    if md5 != "472a2ce52cec8dcbe8b733df55a6c057":
        raise SystemExit("Archive MD5 mismatch; not renaming download")
    temp.rename(target)
    (folder / "archive-download.json").write_text(json.dumps({"url": URL, "size": SIZE, "md5": md5, "sha256": sha256,
        "match": "AP T110XXUANI7 matches; CSC OJV differs from tablet ILO. Do not flash the entire regional package."}, indent=2))
    print("Verified archive: " + str(target), flush=True)

if __name__ == "__main__":
    main()
