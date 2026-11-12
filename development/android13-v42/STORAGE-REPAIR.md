# SM-T110 SYSTEM read-fault repair

Local date: 2026-11-05. Diagnostic evidence: `storage-diagnostics/20261104T215537Z` (folder timestamp is UTC).

The four reproducibly unreadable SYSTEM blocks were restored with their exact contents from the verified matching stock AP. Immediate direct readback passed; the complete dictionary matches the stock SHA-256. After a recovery reboot, a direct read of the entire 7,818,182,656-byte eMMC main area completed with zero read errors. A complete post-repair SYSTEM backup is verified, and stock Android boots and reads the entire dictionary successfully. The storage hold is cleared for controlled kernel testing; the physical cause and long-term reliability remain unproven.

## Evidence before writing

- The stock Android kernel reproduced the failure on a single 4 KB file read. Its saved kernel log records MMC DATA TIMEOUT / error -110 at the affected sectors.
- SYSTEM was unmounted in TWRP. `e2fsck -f -n` completed all five metadata passes with exit 0. This checks filesystem structures; it does not prove that file-data blocks are readable.
- An O_DIRECT scan of the full 1,594,884,096-byte SYSTEM partition identified exactly four unreadable 4 KB blocks. Every other block read successfully.
- All four blocks are inside `/system/hdic/zh.hdb`, inode 1253, extent 249237–250840. The live 256-byte inode matches the stock image byte-for-byte, and the known readable file prefix had already matched stock.
- The eMMC EXT_CSD revision is 7 (eMMC 5.0). PRE_EOL=1 reports normal reserved-block status. Type-A lifetime=6 corresponds to the 50–60% estimated-use band; Type B=0 is undefined. These are coarse counters, not a clean bill of health. [Register interpretation](https://developer.toradex.com/software/linux-resources/linux-features/emmc-linux/).
- A requested clock reduction to 13 MHz left the reported actual clock at 52 MHz. The Marvell source contains timing-mode clock presets. The experiment therefore did not establish low-speed behavior or rule out all controller/bus issues. The requested clock was restored to 52 MHz.

## Exact repair scope

| SYSTEM 4 KB block | Absolute eMMC sector | Dictionary byte offset | Bytes restored |
|---|---|---|---|
| 250715 | 3398360 | 6053888 | 4096 |
| 250728 | 3398464 | 6107136 | 4096 |
| 250730 | 3398480 | 6115328 | 4096 |
| 250731 | 3398488 | 6119424 | 4096 |

Total corrective writes: 16,384 bytes. The payload came from the existing, verified T110XXUANI7 AP image. No CSC change, whole-partition reflash, repartition, wipe or root installer was used. Normal recovery/OS startup can write its own logs and filesystem metadata; the repair tool itself writes only these four whitelisted blocks.

Before writing, the tool checks the exact device CID, SYSTEM start and size, unmounted eMMC filesystems, all four payload checksums and the live dictionary inode. Each 4 KB write uses direct synchronous I/O, `fsync`, and an exact direct readback comparison. A failed operation stops the sequence. The dry-run output and each write result are retained.

The user confirmed there was no personal data requiring preservation. Existing firmware backups and the original incomplete SYSTEM dump remain intact.

## Verification

- All four immediate direct readbacks: passed.
- Post-repair `e2fsck -f -n`: exit 0.
- Full 6,567,404-byte dictionary SHA-256: `dba4c0243ccae87cf6c5a2b917244498b709fb9174c2c02da322bc61dea677d8`, matching stock.
- Reboot into installed TWRP, unmount storage, then O_DIRECT scan of all 7,818,182,656 main-area bytes: zero read errors, 164.91 seconds.
- No MMC DATA TIMEOUT, transfer error -110, I/O error or CRC-error message was found in the kernel log captured after that scan. Initial unsupported-command probing messages are separate from data-read failures.
- The main-area scan includes SYSTEM, USER and the other normal partitions. It does not read internal spare NAND or prove future retention; eMMC boot hardware areas were backed up separately earlier.

The physical cause remains unproven. The rewrite could have refreshed or remapped the affected data internally, but no controller-internal evidence establishes which occurred. A recurring fault should reopen the hardware investigation; repeatedly rewriting or repartitioning would not prove the storage reliable.

## Evidence and tools

`proposed-dictionary-restoration/manifest.json` records exact block coordinates and payload SHA-256/MD5 hashes. `system-read-scan-before.jsonl` is the initial fault map; `whole-emmc-read-scan-after-reboot.jsonl` records the complete clean scan. `restoration-results.json`, `diagnosis.json`, kernel logs and `repair-dry-run.txt` preserve the sequence.

Host scripts: `prepare_dictionary_repair.py`, `backup_repaired_system.py`. Static ARM diagnostic sources: `system_read_probe.c`, `system_read_scan.c`, `emmc_read_scan.c`. `system_block_restore.c` is a deliberately device-, inode- and block-specific repair tool, not a general disk repair utility.
## Final backup and stock boot verification

The complete post-repair SYSTEM snapshot is `backups/20261104T220719Z-repaired-system/SYSTEM.img`, 1,594,884,096 bytes. Its device and host MD5 match (`05d355292f41938ea9a6458d82ac1d26`); SHA-256 is `94ae4e918e9973406f89951824738603e9046940a84c3b83d7d4de96828791ff`. It is explicitly a reconstructed post-repair snapshot. The original incomplete dump is retained without relabeling.

After returning with `/sbin/reboot recovery_done`, stock Android reports `sys.boot_completed=1` and Samsung kernel `3.4.5-2751957`. A second full dictionary pull under that kernel matches the stock SHA-256 above. No experimental kernel was flashed. Machine-readable final status is `storage-diagnostics/LATEST-RESULT.json`.
