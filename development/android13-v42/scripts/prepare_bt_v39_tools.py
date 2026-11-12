from pathlib import Path
p=Path(__file__).resolve().parents[1]
source=(p/'scripts/prepare_bt_v38.py').read_text()
source=source.replace('v38','TEMP39').replace('v37','v38').replace('TEMP39','v39')
source=source.replace('<4*1024*1024','<16*1024*1024').replace("'paired_boot_sha256':None","'paired_boot_sha256':boot['full_boot_sha256']").replace('android13-boot-v44','android13-boot-v45')
(p/'scripts/prepare_bt_v39.py').write_text(source,encoding='utf-8')
s=(p/'scripts/install_bt_v38.py').read_text();s=s.replace('v38','TEMP39').replace('v37','v38').replace('TEMP39','v39')
s=s.replace('android13-boot-v44','android13-boot-v45').replace('37c8eb8b95c8da19e5187ffffa9bde03aa0e17cf53680b819a230007bf554e77','2ca5248c7bc8bf814421cb6d4c6e7c060429a621b66141e5fd4afdbec4b905fa')
s=s.replace(" and boot_meta['paired_system_sha256']==host['sha256']",'')
s=s.replace("json.loads((e/'boot44-installation.json').read_text())['boot_id']","json.loads((e/'v38-installation.json').read_text())['boot_id']")
start=s.index('for f,name,expected in [(boot,');end=s.index("state['status']='REVERSIBLE_PAIR_STAGED_VERIFIED'",start);s=s[:start]+s[end:]
line=" sh(f'dd if={remote}/boot45.img of=/dev/block/mmcblk0p10 bs=4096 count=4096',90);sh('sync',90)\n";assert line in s;s=s.replace(line,'')
line=" sh(f'dd if={remote}/boot44-rollback.img of=/dev/block/mmcblk0p10 bs=4096 count=4096',90);sh('sync',90)\n";assert line in s;s=s.replace(line,'')
s=s.replace('V38_BOOT45_VERIFIED_BOOTING','V39_SYSTEM_VERIFIED_BOOTING').replace('t110-v39-bt-startup-delta','t110-v39-bt-identity-delta')
s=s.replace("recovery_written=False,physical_system_written=False", "recovery_written=False,physical_system_written=False,boot_written=False")
(p/'scripts/install_bt_v39.py').write_text(s,encoding='utf-8')
assert 'dd if={remote}/boot' not in s and 'boot44-installation.json' not in s
print('V39_SCOPED_IMAGE_AND_SYSTEM_ONLY_INSTALLER_PREPARED_REVIEW_BEFORE_RUN')
