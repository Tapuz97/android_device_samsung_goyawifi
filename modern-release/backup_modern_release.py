"""Back up the modernized release draft; do not upload Google/vendor toolkit bytes."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

ROOT = Path(__file__).parent / "lineage14-modern-20261115"
REPO = "Tapuz97/android_device_samsung_goyawifi"
BRANCH = "release/lineage14.1-modern-t110-20261115"
TAG = "t110-lineage14-modern-20261115"
def run(*args, **kwargs):
    return subprocess.check_output(list(map(str, args)), text=True, **kwargs).strip()
def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        while data := source.read(1024 * 1024):
            h.update(data)
    return h.hexdigest()
commit = run("wsl", "-d", "Ubuntu", "--exec", "git", "-C",
             "/root/t110-lineage14-ui/release-modern", "rev-parse", "HEAD")
remote = run("gh", "api", "repos/" + REPO + "/git/ref/heads/" + BRANCH, "--jq", ".object.sha")
assert remote == commit
notes = ROOT / "DRAFT-RELEASE.md"
notes.write_text("""# Modernized LineageOS14.1 for SM-T110 — preparation draft

Both planned editions retain the entire native UI revamp, gestures, icons,
Settings, navigation and lock changes. This is not the old/unmodified UI.

The uploaded ROM transport archive is the Google-free edition, identical to the
owner-confirmed installed system. Extract on the computer; do not flash this ZIP
in TWRP/Odin and do not write physical SYSTEM. Read the installation notes.

A separate Google-enabled candidate has been built locally and passed offline
checks with1847 native files unchanged. Its first boot, setup, Google account,
Play Store and reboot tests remain pending. Google payload bytes and our private
third-party toolkit are intentionally not uploaded in this draft.

The public clean-install/rollback procedure and final source/notice/download
review remain gates. No XDA post has been submitted. Existing working/rollback
images and private data backups remain intact.

Source: https://github.com/""" + REPO + "/tree/" + BRANCH +
                 "\nCommit: " + commit + "\n", encoding="utf-8")
names = [
    ROOT / "SM-T110-Lineage14.1-Modernized-20261115-without-Google-apps.zip",
    ROOT / "ASSETS.json", ROOT / "SHA256SUMS.txt", ROOT / "README.md",
    ROOT / "docs/XDA-POST.md", ROOT / "docs/RELEASE-PLAN.md",
    ROOT / "docs/INSTALLATION.md", ROOT / "verify_modern_package.py",
]
view = subprocess.run(["gh", "release", "view", TAG, "--repo", REPO,
                       "--json", "isDraft,url,assets"], capture_output=True, text=True)
if view.returncode:
    run("gh", "release", "create", TAG, "--repo", REPO, "--target", commit, "--draft",
        "--title", "SM-T110 Modernized LineageOS 14.1 — release preparation",
        "--notes-file", notes)
else:
    assert json.loads(view.stdout)["isDraft"], "Never overwrite a published release"
release = json.loads(run("gh", "release", "view", TAG, "--repo", REPO,
                         "--json", "isDraft,url,assets"))
assert release["isDraft"]
existing = {x["name"]: x for x in release["assets"]}
for path in names:
    assert "PRIVATE" not in path.name and "with-Google-apps" not in path.name
    if path.name not in existing:
        print("Backing up " + path.name, flush=True)
        run("gh", "release", "upload", TAG, path, "--repo", REPO, timeout=1800)
    elif existing[path.name].get("digest"):
        assert existing[path.name]["digest"] == "sha256:" + sha(path)
verified = []
with tempfile.TemporaryDirectory(prefix="t110-release-readback-") as directory:
    for path in names:
        print("Checking online readback " + path.name, flush=True)
        run("gh", "release", "download", TAG, "--repo", REPO,
            "--pattern", path.name, "--dir", directory, timeout=1800)
        assert sha(Path(directory) / path.name) == sha(path)
        verified.append({"name": path.name, "sha256": sha(path)})
receipt = {"status": "PASS_DRAFT_ASSETS_DOWNLOADED_AND_HASH_CHECKED",
           "source_commit": commit, "branch": BRANCH, "tag": TAG, "draft": True,
           "url": release["url"], "assets": verified,
           "google_payload_uploaded": False, "private_userdata_uploaded": False,
           "xda_post_published": False, "tablet_flashed": False}
(ROOT / "ONLINE-VERIFIED.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt), flush=True)
