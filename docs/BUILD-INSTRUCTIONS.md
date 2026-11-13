# Internal-drive LineageOS14.1 build

The Android7.1.2 checkout is /root/t110-lineage14/android in the Ubuntu WSL distro
on C. E is unnecessary. The filesystem was expanded to600GB; around490GiB remained
free during this build. Java8 and Python2 are installed. The task-local host-bin
selects Python2 and starts Jack with a Java security exception limited to its
local authenticated TLS server, keeping ordinary Java settings unchanged.
Never export Jack's private keys or account credentials with source records.

Use scripts/build_rom.sh from Ubuntu to rebuild systemimage and bootimage.
This script does not operate the tablet. Exact upstream revisions and all seven
component diffs are exported by scripts/export_lineage14_source.py. It also saves
new Java/C/C++ files that a plain git diff would omit. Those exports and the actual
device source are canonical; early prepare scripts are historical transformations
and must not be rerun over the integrated checkout.

The official cm-14.1 ARM WebView repository used Git LFS. Run git lfs pull for
webview.apk in external/chromium-webview/prebuilt/arm if restoring a fresh checkout.
Its expected SHA256 is feeedd44677f5643e2de2de4a44061f7bd31a662e78909d6e052b4fe1468870a,
size83580708. Other architecture WebViews are not needed for the ARM32 T110 build.

After a successful final make, run scripts/package_lineage14.py with Python3 inside
Ubuntu. It requires the original private inputs and preservation checkpoint,
validates actual installed vendor hashes and dependency closures, checks the
new Android7 product, wraps its ramdisk with the matched bootstrap/kernel and
checks the complete raw system filesystem. It fails on missing/old shadow libraries.
The finished pair is /root/t110-lineage14/artifacts/lineage14-first-build/boot.img
and system.raw.img, with build-verification.json and filesystem-check.txt.

IMPORTANT: raw out/target/product/goyawifi/boot.img is the ordinary unwrapped
build output and is NOT the installable loop-system package. Only use the matched
pair in artifacts after its verification passes. Never write physical SYSTEM p15.
The intended system file is /data/local/tmp/t110-lineage14-system.raw and its
isolated data directory is /data/local/tmp/t110-lineage14-data. Preserve the existing
TWRP and the Android13 rollback checkpoint. Verify tablet identity, recovery mode,
partition geometry and free space before any installation.

Use FUNCTIONAL-TESTS-LINEAGE14.md for the first real hardware pass. Compilation,
ELF symbol resolution and static ABI checks do not establish working hardware.
The first candidate is permissive/userdebug, without Google apps. GPS integration
and the button LED backend are explicitly pending; see their evidence documents.
