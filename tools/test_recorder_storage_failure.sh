#!/system/bin/sh
set -e
original=/sdcard/Music/SoundRecords
saved=/sdcard/Music/SoundRecords.t110-test-preserved
[ -d "$original" ]
[ ! -e "$saved" ]
mv "$original" "$saved"
restore() {
    if [ -f "$original" ]; then rm "$original"; fi
    if [ ! -e "$original" ]; then mv "$saved" "$original"; fi
}
trap restore EXIT HUP INT TERM
touch "$original"
input tap 300 775
sleep 3
uiautomator dump /data/local/tmp/t110-recorder-storage-failure.xml
pidof org.lineageos.recorder
cat /proc/asound/card0/pcm0c/sub0/status
