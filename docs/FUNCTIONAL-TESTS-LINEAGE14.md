# Lineage14 first full-ROM functional checks

All hardware results start UNTESTED for this new ROM. Android13 observations and
offline component checks do not count as Nougat hardware passes.

Run these on one full boot where possible. Keep continuous screen streaming and
periodic file-log snapshots off during performance checks. Collect bounded logs
after an error; do not reflash/reboot after every individual check.

| Area | Required observation | Status |
|---|---|---|
| Boot | Actual setup/home screen; boot completed; no repeating system-server/SystemUI/launcher crashes | UNTESTED |
| Display | Correct orientation, full panel, text/icons, no stripes, corruption or missing layers | UNTESTED |
| GPU apps | Actual Vivante renderer and accelerated app frames; text, alpha and scrolling visibly correct | UNTESTED |
| Touch | Physical taps, swipes and keyboard selection align across the screen | UNTESTED |
| Physical navigation | Home, Back and left Recents work in hardware mode | UNTESTED |
| Touch navigation | Native Buttons setting enables onscreen bar and disables physical navigation; Power/volume/touch stay functional | UNTESTED |
| Mode persistence | Navigation choice survives a later planned reboot; external/injected navigation remains usable | UNTESTED |
| Button LEDs | Identify actual backend first; visible on/off and real dimming only if supported; independent of navbar selection | BACKEND_UNESTABLISHED |
| Panel brightness | Standard slider changes actual panel brightness without corruption | UNTESTED |
| Wi-Fi | Enable, scan, join the owner's chosen network, transfer data, reconnect after sleep | UNTESTED |
| Bluetooth | Enable, scan, pair; verify selected peripheral function and coexistence with Wi-Fi | UNTESTED |
| Camera | Live changing preview, save and decode a real photograph; clean release/reopen | UNTESTED |
| Audio output | Speaker and volume; wired headphones insert/remove route correctly | UNTESTED |
| Audio input | Record and replay microphone audio; wired microphone if available | UNTESTED |
| Bluetooth audio | Actual A2DP sound and routing, not pairing alone | UNTESTED |
| GPS | Original GPS module is present in firmware; callback/dependency and kernel-node integration remains pending, then actual satellite fix outdoors | INTEGRATION_PENDING |
| Sensors | Actual orientation changes and accelerometer events | UNTESTED |
| Storage | Internal files/media work; microSD detected, safely read/write a disposable test file | UNTESTED |
| USB | Stable ADB; intended MTP/OTG modes only after configuration; external device requires owner accessory | UNTESTED |
| Battery/charging | Plausible battery values and actual charging without a touch/startup regression | UNTESTED |
| Sleep/wake | Visible display, touch and a fresh GPU frame after Power/Home wake; distinguish panel-only blank from whole-system suspend | UNTESTED |
| Suspend soak | Repeated real suspend/wake including USB disconnected; no black panel, touch loss or spontaneous reset | UNTESTED |
| Restart | Native restart/recovery/download actions; physical recovery help required for Download Mode | UNTESTED |
| Memory/performance | JIT enabled, zram active, no continuous diagnostic writes, no recurring ANR during ordinary interaction | UNTESTED |
| Keyboard/search | Normal keyboard enters text; Settings search opens/results without a crash | UNTESTED |
| Browser | Network loading, text input and scrolling; separate app compatibility from driver correctness | UNTESTED |
| Standard Lineage UI | Settings, launcher, Recents/clear-all, notification shade and native wallpaper picker | UNTESTED |

Camera/audio static ABI checks do not prove preview or sound. GPU window swaps
alone do not prove that every application renders correctly. Logical Awake and
ADB access do not prove physical sleep/wake success. No failed physical test may
be marked working using an emulator, an injected tap or a software-renderer fallback.

This initial userdebug build is permissive and uses an unencrypted isolated data
profile. Production security, standard partition OTA/encryption, Google apps and
broader application compatibility require separate qualification. Never write the
faulty physical SYSTEM partition during installation or testing.
