# Recovery provenance check

The original gr8nole T110.TWRP.2.7.0.1.tar.md5 was recovered from our existing
verified backup. SHA256 aa46d7591bc038b24b1062dd8ab39e2567d20a856586dee554f9efdd0b25c8cd.
Its recovery.img is 6946816 bytes. Zero-padding it to the 16 MiB recovery partition
produces f7f0bcf8a0cee4ecf265a2e1d75de028e97e9401c640e8cbc29d4b256d39452e,
which matches the installed recovery partition's SHA256 read on 2026-11-14.
Thus the archived original recovery payload matches the installed recovery bytes,
with only partition padding. No recovery write or reboot was performed.

The old stock-kernel diagnostic is different and is NOT the installed recovery.
It stays in the local historical notes/assets, excluded from the release toolkit.
Archive integrity and an installed match do not establish a new Odin flashing test.
