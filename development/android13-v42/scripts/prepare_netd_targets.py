"""Stage the missing native netd targets against the exact running configuration."""
from pathlib import Path
import difflib,hashlib,json,urllib.request
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35'
base=(e/'boot39.config').read_text()
assert hashlib.sha256(base.encode()).hexdigest()=='144712c4c94a79619da5cdaabcc5e530724ede0f51b42b3accbfa8a4b81c792d'
options=('NETFILTER_XT_MARK','NETFILTER_XT_CONNMARK','NETFILTER_XT_TARGET_IDLETIMER')
candidate=base
for name in options:
    old='# CONFIG_'+name+' is not set';assert candidate.count(old)==1
    candidate=candidate.replace(old,'CONFIG_'+name+'=y')
(e/'netd-targets.config').write_text(candidate,encoding='utf-8',newline='\n')
(e/'netd-targets-config.diff').write_text(''.join(difflib.unified_diff(base.splitlines(True),candidate.splitlines(True),fromfile='BOOT39.config',tofile='BOOT40-candidate.config')),encoding='utf-8',newline='\n')
revision='3c50b450af74d42f8c5d360c692f71002b3bb0af'
name='arch/arm/configs/cyanogenmod_goyawifi_defconfig'
url='https://raw.githubusercontent.com/visyone/android_kernel_samsung_goya/'+revision+'/'+name
before=urllib.request.urlopen(url,timeout=20).read().decode();after=before
for option in options:
    disabled='# CONFIG_'+option+' is not set';enabled='CONFIG_'+option+'=y'
    if disabled in after:after=after.replace(disabled,enabled)
    elif enabled not in after:after+='\n'+enabled+'\n'
patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
(p/'patches/0096-goyawifi-enable-netd-packet-targets.patch').write_text(patch,encoding='utf-8',newline='\n')
(e/'netd-targets-source.json').write_text(json.dumps({'status':'STAGED_NOT_BUILT_OR_INSTALLED',
 'options':options,'running_config_sha256':hashlib.sha256(base.encode()).hexdigest(),
 'candidate_config_sha256':hashlib.sha256(candidate.encode()).hexdigest(),'source_url':url,
 'source_sha256':hashlib.sha256(before.encode()).hexdigest(),
 'reason':'Native networkAddInterface reaches missing MARK target; IDLETIMER also returns RemoteIO. No UID selectors or native networking features removed.'},indent=2)+'\n')
print('NETD_TARGET_CONFIG_STAGED',','.join(options))
for script_name in ('build_netd_targets_kernel.sh','build_gles_audit.sh'):
    script=p/'scripts'/script_name;script.write_bytes(script.read_bytes().replace(b'\r\n',b'\n'))
