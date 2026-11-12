"""Submit only the existing, tested Binder32bit host-ABI fix.

Token is read without echo, retained in process memory, never saved or printed.
"""
from pathlib import Path
import getpass, urllib.request, urllib.error, base64, json, subprocess, os, hashlib

root=Path(__file__).resolve().parents[1]
dest=root/'community/gerrit-soong'
token=getpass.getpass('Temporary Gerrit token (hidden): ')
auth=base64.b64encode(('Tapuz97:'+token).encode()).decode()
def api(path):
    req=urllib.request.Request('https://review.lineageos.org/a/'+path,
                               headers={'Authorization':'Basic '+auth})
    with urllib.request.urlopen(req,timeout=30) as response:
        raw=response.read().decode()
    return json.loads(raw[4:] if raw.startswith(")]}'") else raw)
def git(*args,**kwargs):
    return subprocess.check_output(['git',*args],text=True,**kwargs).strip()

account=api('accounts/self/detail')
assert account['_account_id']==38571 and account.get('username')=='Tapuz97'
agreements=api('accounts/self/agreements')
emails=api('accounts/self/emails')
public='103029727+Tapuz97@users.noreply.github.com'
registered=any(x['email'].lower()==public.lower() for x in emails)
author_email=public if registered else account.get('email') or next((x['email'] for x in emails if x.get('preferred')),None)
if not author_email and len(emails)==1: author_email=emails[0]['email']
print(json.dumps({'email_count':len(emails),'account_has_email':bool(account.get('email')),'author_selected':bool(author_email)}),flush=True)
assert author_email and any(x['email']==author_email for x in emails), 'No verified author email'
assert not author_email.lower().endswith('@intel.com'), 'Work email requires owner choice'
status={'account_id':account['_account_id'],'username':'Tapuz97',
 'agreements':[x.get('name') for x in agreements],
 'public_github_email_registered':registered,'submitted':False}
print(json.dumps(status),flush=True)
branch=api('projects/LineageOS%2Fandroid_build_soong/branches/lineage-20.0')
status['target_branch_revision']=branch['revision']
if not dest.exists():
    subprocess.run(['git','clone','--depth','2','--single-branch','--branch',
                    't110/binder32bit-device-only',
                    'https://github.com/Tapuz97/android_build_soong.git',str(dest)],check=True)
head=git('-C',str(dest),'rev-parse','HEAD')
original='f8d2451b2527ba9e7e2c81f5de9d55341ab10a2f'
changeid='I'+hashlib.sha1(('t110-device-binder32bit:'+original).encode()).hexdigest()
message=('soong: restrict Binder32bit product properties to Android targets\n\n'
 'Binder32bit selects the device kernel Binder ABI. Applying these product\n'
 'properties to native host variants incorrectly gives 64-bit host tools\n'
 'the device Binder pointer width. Skip this product-variable stanza for\n'
 'non-Android targets while retaining the device setting.\n\n'
 'Test: full ARM32 LineageOS 20 SM-T110 system build with Binder32bit enabled\n'
 'Change-Id: '+changeid+'\n')
if head==original or git('-C',str(dest),'log','-1','--format=%ae')!=author_email:
    git('-C',str(dest),'config','user.name','Gal Mitrani')
    git('-C',str(dest),'config','user.email',author_email)
    messagefile=dest/'.git/t110-message.txt';messagefile.write_text(message)
    git('-C',str(dest),'commit','--amend','--no-gpg-sign','--author','Gal Mitrani <'+author_email+'>','-F',str(messagefile))
assert git('-C',str(dest),'show','--format=','--name-only','HEAD')=='android/variable.go'
assert git('-C',str(dest),'show','--format=','--numstat','HEAD')=='5\t0\tandroid/variable.go'
status.update(commit=git('-C',str(dest),'rev-parse','HEAD'),change_id=changeid)
outfile=root/'community/gerrit-soong-status.json'
outfile.write_text(json.dumps(status,indent=2)+'\n')
if not agreements:
    print('READY_LOCALLY: '+('Contributor Agreement not accepted. ' if not agreements else '')+
          ('Public GitHub author email is not registered with Gerrit.' if not registered else ''),flush=True)
    raise SystemExit(2)
askpass=dest/'.git/t110-askpass.cmd'
askpass.write_text('@echo off\r\n"'+os.sys.executable+'" -c "import os;print(os.environ[\'T110_GERRIT_TOKEN\'])"\r\n')
env=os.environ.copy();env.update(T110_GERRIT_TOKEN=token,GIT_ASKPASS=str(askpass),GIT_TERMINAL_PROMPT='0')
try:
    target='https://Tapuz97@review.lineageos.org/LineageOS/android_build_soong'
    # A normal review upload: never force-push or write the protected branch.
    result=subprocess.run(['git','-C',str(dest),'-c','credential.helper=',
                           'push',target,'HEAD:refs/for/lineage-20.0'],env=env,text=True,
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
    output=result.stdout.replace(token,'[REDACTED]')
    print(output,flush=True)
    status.update(submitted=result.returncode==0,push_exit_code=result.returncode,push_output=output)
    outfile.write_text(json.dumps(status,indent=2)+'\n')
finally:
    askpass.unlink(missing_ok=True)
    env.pop('T110_GERRIT_TOKEN',None)
    token='';auth=''
