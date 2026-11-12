from pathlib import Path
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
files=[p/'scripts/prepare_startup_and_restart.py',p/'patches/0094-tests-legacy-netlink-address-flags.patch',Path('/root/t110-build/lineage20/frameworks/libs/net/common/tests/unit/src/com/android/net/module/util/netlink/RtNetlinkAddressMessageTest.java')]
changes={'08000100C0A8446C08000200C0A8446C08000400C0A844FF':'08000100C000026C08000200C000026C08000400C00002FF','192.168.68.108':'192.0.2.108','FE80000000000000025043FFFE02FE01':'FE8000000000000002005EFFFE100001','fe80::250:43ff:fe02:fe01':'fe80::200:5eff:fe10:1','Actual Linux 3.4 RTM_NEWADDR captured after a successful DHCP ACK.':'Captured Linux 3.4 RTM_NEWADDR layout with anonymized addresses.'}
for f in files:
    old=f.read_text();new=old
    for a,b in changes.items():
        assert a in new or b in new,(f,a)
        new=new.replace(a,b)
    f.write_text(new)
print('PUBLIC_TEST_VECTORS_ANONYMIZED')
