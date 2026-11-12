#!/system/bin/sh
set -eu
test -f /init.t110-core.rc
test "$(getprop ro.build.version.release)" = 13
test "$(cat /sys/block/mmcblk0/device/cid)" = 1101003030384745T110_ADB_SERIAL
test "$(getprop service.sf.prime_shader_cache)" = 0
target=/data/local/tmp/t110-fb-composer-v8-test
test ! -e "$target"
mkdir "$target"
cp -a /vendor/lib/. "$target/"
test "$(sha256sum "$target/hw/hwcomposer.mrvl.so" | cut -d' ' -f1)" = 66b02de15b357fb5127846f89288f81aebf5b93701e3d7c999b60922190f1f6f
mv "$target/hw/hwcomposer.mrvl.so" "$target/hw/hwcomposer.mrvl.so.disabled"
setprop ctl.stop surfaceflinger
setprop ctl.stop vendor.hwcomposer-2-1
sleep 2
test "$(getprop init.svc.surfaceflinger)" = stopped
test "$(getprop init.svc.vendor.hwcomposer-2-1)" = stopped
mount -o bind "$target" /vendor/lib
restorecon -RF /vendor/lib
setprop ctl.start vendor.hwcomposer-2-1
sleep 2
setprop ctl.start surfaceflinger
echo FRAMEBUFFER_COMPOSER_TEST_STARTED
