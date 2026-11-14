# Hardware-test1 tool provenance

These are owner-specific engineering session tools, not an end-user installer.
Their original location is `SM-T110/android13-audit`. The shared transport module
belongs at `SM-T110/scripts/recovery_transport.py`; a copy is archived under
`prerequisites` so the old TWRP noninteractive transport is not lost.

Absolute C:/Ubuntu paths, exact image hashes and tablet identity guards are
intentional. Do not run these tools against another device or publish them as a
universal flash package. `install_complete_candidate.py` deliberately requires
the verified old-data archive, preserved14.1 pair and matching recovery state
before reclaiming only the listed userdata test paths.

`monitor_one_boot.py` observes one boot and never restarts the tablet. Frame
captures and logs are bounded. `capture_audio_initialization.py` records one
same-boot audio-service reinitialization after the normal player attempt failed;
that diagnostic is not an as-built audio PASS. See RESULTS.md for actual results.
