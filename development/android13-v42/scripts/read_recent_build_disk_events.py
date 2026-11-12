from pathlib import Path
import datetime,json,subprocess,xml.etree.ElementTree as ET
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35'
query='*[System[(EventID=153 or EventID=129) and TimeCreated[timediff(@SystemTime) <= 600000]]]'
r=subprocess.run(['wevtutil.exe','qe','System','/q:'+query,'/f:xml','/c:8','/rd:true'],capture_output=True,timeout=25)
assert r.returncode==0,r.stderr.decode(errors='replace')
text=r.stdout.decode('utf-8-sig',errors='replace');ns={'e':'http://schemas.microsoft.com/win/2004/08/events/event'}
root=ET.fromstring('<Events>'+text+'</Events>');rows=[]
for event in root:
 rows.append(dict(time=event.find('e:System/e:TimeCreated',ns).get('SystemTime'),provider=event.find('e:System/e:Provider',ns).get('Name'),event_id=event.findtext('e:System/e:EventID',namespaces=ns)))
record=dict(checked=datetime.datetime.now().astimezone().isoformat(),window_minutes=10,events=rows)
(e/'latest-disk-events.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record,indent=2))
