# Applying and checking this audit

The new patches are incremental to the preserved v42/BOOT48 source delta. Do
not apply them to an arbitrary upstream Lineage20 checkout or to Lineage14.1.

1. Restore the original pinned manifest and existing source delta first. Native
   framework upstream is915ad642e331e0f8ea107b5f5519f2c6f1e7e01c; hardware
   interfaces upstream is2f83e1bda9536aaf406352c868a8192cc3526a69. Existing
   checkpoint patches and untracked helpers must be present before these additions.
2. In frameworks/native, check/apply patch0001. In hardware/interfaces,
   check/apply patch0002. Run `git apply --check` before `git apply` in each tree.
3. Re-run current-source host regressions using verify_offline.py. Its default
   paths point at this audit's selected source tree. For a full Android checkout,
   pass `--platform-root /path/to/android` and `--tests /path/to/audit/tests`.
4. Build actual ARM libraries and enforce normal linker, policy and image-content
   checks after the full build context is restored. Host regressions alone are
   insufficient to qualify a ROM or authorize flashing.

The restore/apply/fix/write scripts preserve how this pass was prepared; they are
one-time preparation tools and may reject already-patched source. Use
verify_offline.py for repeatable checks; it reads the current callback bodies,
compiles them against controlled test boundaries and changes no source or images.

No new audio HAL, camera provider or replacement hardware composer has been
activated. Audio's stub and graphics' software fallback remain explicit blockers.
The source contract and feature matrix in README.md guide the next work; they
must not be advertised as implemented or hardware-tested features.
