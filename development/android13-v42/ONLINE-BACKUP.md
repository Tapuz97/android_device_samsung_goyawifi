# T110 online preservation checkpoint

2026-11-12. The eight core archives below have been uploaded to the private
unpublished draft release443063640 in Tapuz97/android_device_samsung_goyawifi,
downloaded again and verified against their complete SHA256 values.
Anonymous release and asset access returned404. Keep the draft unpublished.

The complete project restoration stream passed all67,743 member hashes.
All25 changed Android-project base commits were independently verified online.
The final metadata capsule also passed a complete member readback and an
authenticated download/SHA256 check. All nine required payloads are verified:
6,299,404,805 bytes in total. Final source operations are captured by device
commit efe363e0f1358c52c678e41406851b811aad0188 and kernel commit
3eb98fe728aefa780638a1bb2f487e19ba6fadcb.

| Asset | Bytes | SHA256 |
|---|---:|---|
| android13-current-private.tar.gz | 1227122304 | 1a96a8aa56cd12ceec608990fda019e896699f549a23799df114a92f94732c3c |
| kernel-source-private.tar.gz | 137908689 | 5386fcdf3b54dfe1b4ca4a60474d62e40f2da9e86dffcb3b7fcae876c8e475f6 |
| lineage20-source-delta-private.tar.gz | 3153965 | 1be195bfbd0a73be2ebe551708be1e5f56b0b9f3c30164c201cb1e38a0e4a88d |
| T110Build-host-fixtures-private.tar.gz | 2013247 | b19e60ac205315077b5c3fef8d651d8be5071eb48b97dfa2eff3772749e1fefc |
| Ubuntu-host-fixtures-private.tar.gz | 17769788 | a702f73528503a47ff1c1e104dc5771738bc8959427c813db375690f923d34ce |
| project-restoration-private.tar.gz.part000 | 1879048192 | f54552ed268bcdb94ead15c87f894de003a2a140e1739c39b3b36ac6edf64d73 |
| project-restoration-private.tar.gz.part001 | 1879048192 | 1ca77bb7148c018464941dc22bb195b8a6b59178739a11080c60ff162a0ca493 |
| project-restoration-private.tar.gz.part002 | 1149151458 | a30a09ec55eb8cf4ed2339f997016a6f519d0a1720f9df9847fbbe478f0ae842 |
| final-metadata-private.tar.gz | 4188970 | 10ac536e0a94aa2cfb2ba7db592309891e601ba56efb69e1676d1b36b905fa3d |

The numbered parts are one gzip/tar stream. Join them in order before extraction.
Restore instructions and authenticated download command: RESTORE.md.
Repository, draft release and review links: LINKS.md.

The final metadata's anonymous API check was rate-limited403 (quota0), not
counted as a successful privacy test. Its direct anonymous download URL returned404,
and authenticated server metadata confirmed the release remains an unpublished
draft. Every payload's downloaded byte count and SHA256 passed independently.

FINAL-ONLINE-VERIFIED.json is the separate machine-readable verification record.
Its asset list covers these nine payloads, excluding that record itself.
The record was also uploaded, downloaded and hash-verified:2344 bytes,
SHA25699b4ca48608d40bdedf5219a4f79c6488d514ed61ecb3cf1f2fdf84e9b13ccd3.
