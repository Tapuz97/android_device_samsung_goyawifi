"""Check audio access in the compiled SELinux policy, not only source text."""
from pathlib import Path
import json
import sys

root = Path('/root/t110-android13')
sys.path.insert(0, str(root / 'android/system/sepolicy/tests'))
from policy import Policy

product = root / 'out/target/product/t110_bringup'
lib = root / 'out/soong/.intermediates/system/sepolicy/tests/libsepolwrap/linux_glibc_x86_64_shared/libsepolwrap.so'
binary = product / 'system/vendor/etc/selinux/precompiled_sepolicy'
fc = [product / 'system/etc/selinux/plat_file_contexts', product / 'system/vendor/etc/selinux/vendor_file_contexts']
policy = Policy(str(binary), [str(p) for p in fc], str(lib))
checks = []
for source, target, klass, required in (
    ('hal_audio_default', 't110_audio_textrel_file', 'file', {'read', 'open', 'execute', 'map', 'execmod'}),
    ('hal_audio_default', 'proc_t110_audio_clock', 'file', {'read', 'open', 'write'}),
    ('init', 'proc_t110_audio_clock', 'file', {'read', 'open', 'write', 'setattr'}),
    ('hal_audio_default', 'audio_config_prop', 'file', {'read', 'open', 'map'}),
    ('hal_audio_default', 'vendor_configs_file', 'file', {'read', 'open'}),
    ('hal_audio_default', 'system_file', 'file', {'read', 'open'}),
):
    rules = list(policy.QueryTERule(scontext={source}, tcontext={target}, tclass={klass}))
    permitted = set().union(*(r.perms for r in rules))
    assert required <= permitted, (source, target, required - permitted)
    checks.append(dict(source=source, target=target, klass=klass, required=sorted(required), status='PASS'))

audio_domains = policy.QueryTypeAttribute('hal_audio_server', True)
types = policy.GetAllTypes(False)
allowed_sources = set()
for rule in policy.QueryTERule(tcontext={'t110_audio_textrel_file'}, tclass={'file'}, perms={'execmod'}):
    allowed_sources.update({rule.sctx} if rule.sctx in types else policy.QueryTypeAttribute(rule.sctx, True))
assert allowed_sources <= audio_domains, allowed_sources - audio_domains
assert allowed_sources == {'hal_audio_default'}, allowed_sources
checks.append(dict(check='DSP execmod restricted to hal_audio_default', status='PASS', sources=sorted(allowed_sources)))
result = dict(status='PASS', binary=str(binary), checks=checks, hardware_tested=False)
Path('/root/t110-android13-audit/compiled-audio-policy.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS compiled policy: clock access, properties, config reads and audio-only DSP relocations.')
