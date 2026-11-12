"""Local, view-only framebuffer feed; no tablet input or display writes."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from PIL import Image
import io, json, os, subprocess, threading, time

p=Path(__file__).resolve().parents[1]
out=p/'hardware-tests/20261107-200616-core/live-feed'
out.mkdir(exist_ok=True)
adb=[str(Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'),'-s','T110_ADB_SERIAL']
state={'data':None,'message':'Connecting to tablet','sequence':0,'captured_at':None}
lock=threading.Lock()

def call(command,raw=False):
    r=subprocess.run(adb+(['exec-out'] if raw else ['shell'])+[command],capture_output=True,timeout=8)
    if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace').strip() or 'USB disconnected')
    return r.stdout

def capture():
    assert call('cat /sys/block/mmcblk0/device/cid').decode().strip()=='1101003030384745T110_ADB_SERIAL'
    while True:
        start=time.monotonic()
        try:
            geometry=call('cat /sys/class/graphics/fb0/virtual_size /sys/class/graphics/fb0/bits_per_pixel /sys/class/graphics/fb0/stride /sys/class/graphics/fb0/pan').decode().splitlines()
            assert geometry[:3]==['1024,1200','32','4096'],geometry
            assert geometry[3] in ['0,0','0,600'],geometry
            offset=600 if geometry[3]=='0,600' else 0
            raw=call(f'dd if=/dev/graphics/fb0 bs=4096 skip={offset} count=600 2>/dev/null',True)
            if len(raw)==0:raise RuntimeError('Screen asleep — press Power briefly on the tablet')
            assert len(raw)==4096*600,len(raw)
            # The panel's native scanout is rotated 270 degrees from portrait.
            frame=Image.frombytes('RGB',(1024,600),raw,'raw','BGRX').transpose(Image.Transpose.ROTATE_270)
            buf=io.BytesIO();frame.save(buf,format='JPEG',quality=88)
            data=buf.getvalue()
            with lock:
                seq=state['sequence']+1
                state.update(data=data,message='Live · view only',sequence=seq,captured_at=time.time())
                meta={k:v for k,v in state.items() if k!='data'}
            temporary=out/'latest.tmp';temporary.write_bytes(data);temporary.replace(out/'latest.jpg')
            (out/'status.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
        except Exception as e:
            with lock:state['message']=str(e)
        time.sleep(max(0.05,0.65-(time.monotonic()-start)))

html='''<!doctype html><meta charset="utf-8"><title>SM-T110 live screen</title>
<style>body{margin:0;background:#141719;color:#eee;font:16px system-ui;text-align:center}
header{padding:12px}h1{font-size:20px;margin:0 0 4px}#status{color:#b7c6ce}img{height:calc(100vh - 90px);max-width:100%;object-fit:contain;background:#000}small{display:block;color:#9faeb6}</style>
<header><h1>SM-T110 live screen</h1><span id="status">Connecting…</span><small>Use the tablet normally. This window only shows its screen.</small></header><img id="screen">
<script>let busy=false;async function refresh(){if(busy)return;busy=true;try{let s=await(await fetch('/status?t='+Date.now())).json();document.querySelector('#status').textContent=s.message+' · frame '+s.sequence;let r=await fetch('/frame.jpg?t='+s.sequence);if(r.ok){let old=document.querySelector('#screen').src;document.querySelector('#screen').src=URL.createObjectURL(await r.blob());if(old.startsWith('blob:'))URL.revokeObjectURL(old);}}finally{busy=false}}setInterval(refresh,650);refresh();</script>'''

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        with lock:
            if self.path.startswith('/frame.jpg'):
                data=state['data'];kind='image/jpeg'
            elif self.path.startswith('/status'):
                data=json.dumps({k:v for k,v in state.items() if k!='data'}).encode();kind='application/json'
            else:data=html.encode();kind='text/html; charset=utf-8'
        self.send_response(200 if data else 503)
        self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.end_headers()
        if data:
            try:self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):pass
    def log_message(self,*args):pass

server=ThreadingHTTPServer(('127.0.0.1',8765),Handler)
(out/'server.json').write_text(json.dumps({'pid':os.getpid(),'url':'http://127.0.0.1:8765/','device_writes':False}),encoding='utf-8')
threading.Thread(target=capture,daemon=True).start()
print('http://127.0.0.1:8765/',flush=True)
server.serve_forever()
