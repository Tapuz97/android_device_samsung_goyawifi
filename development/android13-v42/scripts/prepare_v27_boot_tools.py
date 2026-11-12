"""Prepare the proven kernel-only packager and independent verifier for v27."""
from pathlib import Path

p = Path(__file__).resolve().parents[1]
s = (p/'scripts/package_v25_boot.py').read_text()
s = s.replace('verified v24 boot', 'verified v26 boot')
s = s.replace("old=p/'artifacts/android13-full-v24'; dest=p/'artifacts/android13-full-v25'",
              "old=p/'artifacts/android13-full-v26'; dest=p/'artifacts/android13-full-v27'")
s = s.replace('artifacts/kernel-binder-secctx', 'artifacts/kernel-storage-acl')
s = s.replace("parent='../android13-full-v24'", "parent='../android13-full-v26'")
s = s.replace("['Binder security-context kernel','Matching rebuilt galcore module']",
              "['Enable ext4 POSIX ACL for FUSE-backed user storage','Matching rebuilt galcore module']")
s = s.replace('Packaged v25 kernel/module', 'Packaged v27 storage ACL kernel/module')
s += '''
system = json.loads((p/'artifacts/lineage20-rom-v18/host-verification.json').read_text())
assert system['status'] == 'VERIFIED'
assert json.loads((p/'evidence/offline-v27/contents.json').read_text())['status'] == 'PASS'
assert json.loads((p/'evidence/offline-v28/kernel-verification.json').read_text())['acl_code_linked']
pair = dict(status='PACKAGED_NOT_BOOT_TESTED', system_artifact='../lineage20-rom-v18/system.raw.img',
            system_sha256=system['sha256'], system_md5=system['md5'], system_bytes=system['bytes'],
            boot_sha256=sha(full), boot_md5=hashlib.md5(full).hexdigest(),
            kernel_sha256=sha(newkernel), module_sha256=sha(module),
            bootstrap_policy_sha256=oldprov['bootstrap_policy_sha256'],
            hardware_tested=False, hardware_validated=False, full_boot_passed=False,
            fixes=['All v18 system fixes retained', 'Ext4 POSIX ACL enabled in kernel'],
            limits=['Storage mount and usable UI require hardware validation', 'Wi-Fi radio remains unported'])
(dest/'system-pair.json').write_text(json.dumps(pair, indent=2)+'\\n')
'''
(p/'scripts/package_v27_boot.py').write_text(s)
verifier = (p/'scripts/verify_v26_boot.py').read_text().split("old = unpack(", 1)[0]
verifier += '''old = unpack(p/'artifacts/android13-full-v26/KERNEL.img')
new = unpack(p/'artifacts/android13-full-v27/KERNEL.img')
dest = p/'artifacts/android13-full-v27'
pair = json.loads((dest/'system-pair.json').read_text())
prov = json.loads((dest/'provenance.json').read_text())
kernel = p/'artifacts/kernel-storage-acl'
assert sha(new[0]) == pair['boot_sha256'] == prov['full_boot_sha256']
assert hashlib.md5(new[0]).hexdigest() == pair['boot_md5']
assert new[1] == (kernel/'zImage').read_bytes() and old[1] != new[1]
assert old[4] == new[4] and set(old[3]) == set(new[3])
changed = sorted(k for k in old[3] if old[3][k] != new[3][k])
assert set(changed).issubset({'lib/modules/galcore.ko'})
assert new[3]['lib/modules/galcore.ko'] == (kernel/'galcore.ko').read_bytes()
assert sha(new[3]['lib/modules/galcore.ko']) == pair['module_sha256']
for name, digest in prov['unchanged_ramdisk_files'].items():
    assert sha(new[3][name]) == digest
assert sha(new[3]['t110-preload-policy']) == pair['bootstrap_policy_sha256']
assert new[3]['t110-preload-policy'] == (p/'evidence/offline-v26/embedded-policy.bin').read_bytes()
assert new[0][:new[5]] == (dest/'boot.img').read_bytes()
assert new[2] == (dest/'ramdisk.cpio.gz').read_bytes()
assert new[0][12:16] == old[0][12:16] and new[0][20:576] == old[0][20:576]
assert 'CONFIG_EXT4_FS_POSIX_ACL=y' in (kernel/'kernel.config').read_text()
result = dict(status='PASS', boot_sha256=sha(new[0]), boot_md5=pair['boot_md5'],
              changed_ramdisk_files=changed, kernel_changed=True,
              cpio_metadata_unchanged=True, embedded_policy_matches_system=True,
              header_id_verified=True, partition_bytes=len(new[0]),
              android_boots=0, tablet_access=False)
(p/'evidence/offline-v28/boot-verification.json').write_text(json.dumps(result, indent=2)+'\\n')
pair['status'] = 'OFFLINE_VERIFIED_NOT_BOOT_TESTED'
(dest/'system-pair.json').write_text(json.dumps(pair, indent=2)+'\\n')
print(json.dumps(result, indent=2))
'''
verifier = verifier.replace('v26 contents', 'v27 contents')
(p/'scripts/verify_v27_boot.py').write_text(verifier)
print('Prepared v27 kernel-only packager and verifier; no packaging or tablet access yet.')
