"""Publish isolated, verified source contributions using the owner's local GH login."""
from pathlib import Path
import base64,difflib,hashlib,itertools,json,os,subprocess,tempfile,time

p=Path(__file__).resolve().parents[1];e=p/'community';e.mkdir(exist_ok=True)
owner='Tapuz97';author={'name':'Gal Mitrani','email':'103029727+Tapuz97@users.noreply.github.com'}
record={}
def save():(e/'contributions.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
def api(path,method='GET',data=None,missing=False):
    args=['gh','api',path,'--method',method]
    if data is not None:args+=['--input','-']
    r=subprocess.run(args,input=json.dumps(data) if data is not None else None,text=True,encoding='utf-8',capture_output=True,timeout=90)
    if missing and r.returncode and 'HTTP 404' in r.stderr:return None
    if r.returncode:raise RuntimeError(r.stderr[:1000])
    return json.loads(r.stdout) if r.stdout.strip() else None
assert api('user')['login']==owner
def file(repo,path,ref):
    r=api(f'repos/{repo}/contents/{path}?ref={ref}')
    return base64.b64decode(r['content'])
def head(repo):return api(f'repos/{repo}/git/ref/heads/lineage-20.0')['object']['sha']
def fork(upstream):
    name=upstream.split('/')[1];repo=owner+'/'+name
    r=api('repos/'+repo,missing=True)
    if r is None:
        api('repos/'+upstream+'/forks','POST',{'default_branch_only':True})
        for _ in range(45):
            r=api('repos/'+repo,missing=True)
            if r and r.get('parent',{}).get('full_name')==upstream:break
            time.sleep(2)
        else:raise RuntimeError('Fork not ready: '+repo)
    assert r['parent']['full_name']==upstream and not r['private']
    return repo
def branch(repo,name,base,changes,title,body):
    current=api(f'repos/{repo}/git/ref/heads/{name}',missing=True)
    if current:
        sha=current['object']['sha'];commit=api(f'repos/{repo}/git/commits/{sha}')
        assert commit['parents'][0]['sha']==base,'Existing branch differs; do not overwrite'
        for path,data in changes.items():assert file(repo,path,sha)==data.encode('utf-8'),path
        return sha
    treebase=api(f'repos/{repo}/git/commits/{base}')['tree']['sha']
    tree=api(f'repos/{repo}/git/trees','POST',{'base_tree':treebase,'tree':[{'path':path,'mode':'100644','type':'blob','content':data} for path,data in changes.items()]})
    commit=api(f'repos/{repo}/git/commits','POST',{'message':title+'\n\n'+body,'tree':tree['sha'],'parents':[base],'author':author,'committer':author})
    api(f'repos/{repo}/git/refs','POST',{'ref':'refs/heads/'+name,'sha':commit['sha']})
    for path,data in changes.items():assert file(repo,path,commit['sha'])==data.encode('utf-8'),path
    return commit['sha']
def pr(upstream,name,title,body,draft=False):
    existing=api(f'repos/{upstream}/pulls?state=all&head={owner}:{name}&base=lineage-20.0')
    if existing:return existing[0]['html_url']
    return api(f'repos/{upstream}/pulls','POST',{'title':title,'body':body,'head':owner+':'+name,'base':'lineage-20.0','draft':draft,'maintainer_can_modify':True})['html_url']

# Reuse the already-published fork branch; do not add a duplicate branch or rewrite it.
k='visyone/android_kernel_samsung_goya';ours=owner+'/android_kernel_samsung_goya'
kpath='arch/arm/mach-mmp/onboard/Lcd_mipi2lvds_vx5b3d.c';base=head(k)
assert base=='3c50b450af74d42f8c5d360c692f71002b3bb0af'
before=file(k,kpath,base);after=file(ours,kpath,'t110/preserve-i2c-on-fb-blank')
with tempfile.TemporaryDirectory(prefix='goya-source-review-') as temp:
    temp=Path(temp);target=temp/kpath;target.parent.mkdir(parents=True);target.write_bytes(before)
    patch=p/'patches/0061-kernel-goya-preserve-shared-i2c-on-fb-blank.patch'
    for extra in [['--check'],[]]:subprocess.run(['git','-C',str(temp),'apply',*extra,str(patch)],check=True,capture_output=True)
    assert target.read_bytes().replace(b'\r\n',b'\n')==after.replace(b'\r\n',b'\n'),'Published branch must match the installed source patch'
text=after.decode('utf-8');needle='#if defined(CONFIG_QUICKLOGIC_BRIDGE) && \\\n\t(!defined(CONFIG_MACH_GOYA) || defined(CONFIG_HAS_EARLYSUSPEND))'
assert needle in text
snippet=needle+'\nREROUTE\n#else\nKEEP_I2C\n#endif\n'
matrix=[]
for quick,goya,early in itertools.product([False,True],repeat=3):
    args=['gcc','-E','-P','-x','c','-']
    for macro,on in [('CONFIG_QUICKLOGIC_BRIDGE',quick),('CONFIG_MACH_GOYA',goya),('CONFIG_HAS_EARLYSUSPEND',early)]:
        if on:args+=['-D'+macro]
    r=subprocess.run(args,input=snippet,text=True,capture_output=True,check=True)
    expected='REROUTE' if quick and (not goya or early) else 'KEEP_I2C'
    assert r.stdout.strip()==expected
    matrix.append({'quicklogic':quick,'goya':goya,'early_suspend':early,'result':expected})
compare=api(f'repos/{ours}/compare/{base}...t110/preserve-i2c-on-fb-blank')
assert len(compare['files'])==1 and compare['files'][0]['filename']==kpath
assert compare['files'][0]['additions']==9 and compare['files'][0]['deletions']==2
record['kernel']={'status':'VALIDATED','upstream':k,'branch':'t110/preserve-i2c-on-fb-blank','base':base,'head':compare['commits'][-1]['sha'],'files':1,'additions':9,'deletions':2,'preprocessor_matrix':matrix};save()
body='''On GOYA, the VX5B3D framebuffer blank path remuxes I2C1 to GPIO even when the BT532 touchscreen remains active. With CONFIG_HAS_EARLYSUSPEND disabled, Android framebuffer blanking can leave touch transfers timing out and prevent the display bridge from waking.

Keep the bus mux intact for GOYA without early suspend. Existing early-suspend configurations and other boards retain their original path; the touch/system PM pin handling is unchanged.

Validation:
- Exact net source change matches the patch compiled into our SM-T110 Android 13 bring-up kernel and used for display blank/wake testing. That kernel also contains other compatibility backports; this is not a claim of a standalone full-ROM port.
- Real GCC preprocessing checked all eight QUICKLOGIC_BRIDGE / MACH_GOYA / HAS_EARLYSUSPEND combinations, including preservation of the legacy paths.
- Patch application checked against upstream lineage-20.0 at 3c50b450af74d42f8c5d360c692f71002b3bb0af. Net diff is one file, 9 insertions and 2 deletions. An existing follow-up commit fixes line endings; the combined diff has no whole-file conversion.

Other GOYA variants, battery drain and full system suspend have not been independently qualified. The separate charger-mode touchscreen registration workaround is deliberately excluded from this PR.'''
record['kernel']['pull_request']=pr(k,'t110/preserve-i2c-on-fb-blank','goya: preserve shared I2C when blanking without early suspend',body);save();print('KERNEL_PR '+record['kernel']['pull_request'],flush=True)

# Device-name key maps proven in the running bring-up product; preserve legacy maps.
d='visyone/android_device_samsung_goyawifi';base=head(d);repo=fork(d)
assert base=='77bcf94a6f2e6e4497b0ec9a8aecd1915f4fc05c'
path='device_goyawifi.mk';old=file(d,path,base).decode('utf-8')
needle='    $(LOCAL_PATH)/keylayout/sec_touchkey.kl:system/usr/keylayout/sec_touchkey.kl'
assert old.count(needle)==1
new=old.replace(needle,needle+' \\\n    $(LOCAL_PATH)/keylayout/gpio-keys.kl:system/usr/keylayout/gpio-keys.kl \\\n    $(LOCAL_PATH)/keylayout/sec_touchscreen.kl:system/usr/keylayout/sec_touchscreen.kl')
changes={path:new}
for name in ['gpio-keys.kl','sec_touchscreen.kl']:
    source=(p/'work/device/samsung/t110_bringup/keylayout'/name).read_text()
    rows=[line.split() for line in source.splitlines() if line.strip() and not line.startswith('#')]
    expected={'gpio-keys.kl':[['key','102','HOME'],['key','114','VOLUME_DOWN'],['key','115','VOLUME_UP']], 'sec_touchscreen.kl':[['key','139','APP_SWITCH'],['key','158','BACK']]}[name]
    assert rows==expected
    changes['keylayout/'+name]='# SPDX-License-Identifier: Apache-2.0\n# Copyright (C) 2026 Gal Mitrani\n\n'+source
name='t110/board-navigation-keymaps'
sha=branch(repo,name,base,changes,'goyawifi: map GPIO and touchscreen navigation keys','Install maps matching the actual gpio-keys and sec_touchscreen input names.\nRetain the legacy sci-keypad/sec_touchkey maps for older kernel naming.\n\nMappings match the ones built into the tested Android 13 bring-up product.\nThe upstream product as a whole has not been rebuilt or qualified.')
record['device_tree']={'repository':repo,'branch':name,'base':base,'commit':sha,'validation':'Mapping contents match hardware-validated bring-up product; upstream product not rebuilt'};save()
body='''The SM-T110 kernel exposes the physical Home/volume keys as `gpio-keys` and the capacitive navigation keys as `sec_touchscreen`. The current tree only installs `sci-keypad.kl` and `sec_touchkey.kl`, so these actual input devices fall back to generic mappings.

Add and install matching maps:
- GPIO: Linux 102 -> HOME, 114 -> VOLUME_DOWN, 115 -> VOLUME_UP.
- Touchscreen: Linux 139 -> APP_SWITCH, 158 -> BACK.

Retain the existing legacy maps for older kernel input names. The map contents are the same as those compiled into our SM-T110 Android 13 bring-up image; the device owner physically confirmed Home, Back and left Recents all work. New file comments do not change the mappings.

The complete upstream product has not been rebuilt: our validation uses the separate bring-up product and patched kernel. This PR only contributes the board key maps, not a claim that the whole existing tree now boots. Hardware/onscreen navigation mutual exclusion is a separate framework policy change and is not implemented by these files.'''
record['device_tree']['pull_request']=pr(d,name,'goyawifi: install keymaps for the actual navigation input devices',body);save();print('DEVICE_PR '+record['device_tree']['pull_request'],flush=True)

# Generic Lineage candidate: publish a fork branch, not an incorrectly routed GH PR.
s='LineageOS/android_build_soong';base=head(s);repo=fork(s);path='android/variable.go'
old=file(s,path,base).decode('utf-8')
needle='''		name := variableValues.Type().Field(i).Name
		property := "product_variables." + proptools.PropertyNameForField(name)'''
replacement='''		name := variableValues.Type().Field(i).Name
		// Binder32bit selects the device kernel ABI. Native host tools must
		// retain their own pointer width even for a 32-bit Binder product.
		if name == "Binder32bit" && mctx.Os() != Android {
			continue
		}
		property := "product_variables." + proptools.PropertyNameForField(name)'''
assert old.count(needle)==1
new=old.replace(needle,replacement)
name='t110/binder32bit-device-only'
sha=branch(repo,name,base,{path:new},'soong: limit Binder32bit product flags to Android targets','Binder32bit selects the device kernel ABI. Applying it to native host\ntools changes their Binder ABI based on the product instead of their\nnative pointer width. Keep that product variable specific to Android.\n\nUsed in successful SM-T110 LineageOS 20 host/target system builds.\nDevice Binder structures stay 32-bit and native host structures 64-bit.\n\nOfficial LineageOS submission is pending Gerrit account/Contributor\nAgreement setup and maintainer review; this fork is not an upstream merge.')
record['lineage_candidate']={'repository':repo,'branch':name,'commit':sha,'base':base,'tested_manifest_soong_revision':'c80e6e3b82f2c0fded69b44b514d4c4d5519c9b5','upstream_submission':'NOT_SUBMITTED: Gerrit credentials and owner-accepted Contributor Agreement required','url':f'https://github.com/{repo}/tree/{name}'};save();print('LINEAGE_CANDIDATE '+record['lineage_candidate']['url'],flush=True)
