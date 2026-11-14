from pathlib import Path
import json
import sys

root=Path('/root/t110-android13');audit=Path('/root/t110-android13-audit')
sys.path.insert(0,str(root/'android/system/sepolicy/tests'))
from policy import Policy
image=audit/'complete-image/extracted'
lib=root/'out/soong/.intermediates/system/sepolicy/tests/libsepolwrap/linux_glibc_x86_64_shared/libsepolwrap.so'
contexts=[image/'system/etc/selinux/plat_file_contexts',image/'system/vendor/etc/selinux/vendor_file_contexts']
p=Policy(str(image/'system/vendor/etc/selinux/precompiled_sepolicy'),[str(x) for x in contexts],str(lib))
records=[]
def perms(source,target,kind):
    rules=p.QueryTERule(scontext={source},tcontext={target},tclass={kind})
    return set().union(*(r.perms for r in rules))
for source,target,kind,required in (
    ('vendor_init','proc_t110_audio_clock','file',{'read','open','setattr'}),
    ('vendor_init','audio_config_prop','property_service',{'set'}),
    ('hal_audio_default','proc_t110_audio_clock','file',{'read','write','open'}),
    ('hal_audio_default','audio_config_prop','file',{'read','open','map'}),
    ('hal_audio_default','exported_default_prop','file',{'read','open','map'}),
    ('untrusted_app','gpu_device','chr_file',{'open','read','write','ioctl','map'}),
    ('platform_app','gpu_device','chr_file',{'open','read','write','ioctl','map'}),
    ('system_app','gpu_device','chr_file',{'open','read','write','ioctl','map'}),
    ('surfaceflinger','gpu_device','chr_file',{'open','read','write','ioctl','map'}),
    ('hal_graphics_allocator_default','gpu_device','chr_file',{'open','read','write','ioctl','map'}),
    ('hal_graphics_composer_default','gpu_device','chr_file',{'open','read','write','ioctl','map'}),
):
    actual=perms(source,target,kind)
    assert required<=actual,(source,target,required-actual)
    records.append(dict(source=source,target=target,kind=kind,required=sorted(required),status='PASS'))
assert not ({'read','write'}&perms('untrusted_app','graphics_device','chr_file'))
paths=p.QueryFc('gpu_device')
assert '/dev/graphics/galcore' in paths,paths
result=dict(status='PASS',scope='Actual image policy and file-context inputs; no live SELinux enforcement',
    checks=records,gpu_exact_path_present=True,unrelated_graphics_device_not_opened_to_apps=True,
    vendor_init_actual_action_actor_checked=True,flashed=False)
(audit/'complete-image-policy-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS image policy: actual vendor-init audio actions and exact GPU-node app/HAL access; generic graphics restriction retained.')
