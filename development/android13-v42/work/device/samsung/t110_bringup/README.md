# T110 native userspace bootstrap

Build-only Android 13 ARM product for the first bionic/init/ADB compatibility steps. It does not inherit the legacy Marvell platform-library replacements. It is not a complete LineageOS ROM and does not create an authorized flash image by itself. The first target is `t110_bionic_probe`; build init/adbd next after resolving actual dependency and kernel compatibility failures. The tested kernel and original stock rollback stay separate.
