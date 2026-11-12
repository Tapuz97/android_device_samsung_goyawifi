"""Read only: determine whether this account can create an archive project."""
import getpass,urllib.request,base64,json
from pathlib import Path
token=getpass.getpass('Temporary Gerrit token (hidden): ')
req=urllib.request.Request('https://review.lineageos.org/a/accounts/self/capabilities',headers={'Authorization':'Basic '+base64.b64encode(('Tapuz97:'+token).encode()).decode()})
with urllib.request.urlopen(req,timeout=30) as response:raw=response.read().decode()
data=json.loads(raw[4:]);result={k:bool(data.get(k,False)) for k in ['createProject','administrateServer','createGroup','viewAllAccounts']}
result['can_create_backup_repository']=result['createProject'];result['performed_project_creation']=False
Path('community/gerrit-archive-capabilities.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
