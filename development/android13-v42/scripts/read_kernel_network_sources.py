from pathlib import Path
import subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35'
for f in ['net/ipv4/fib_semantics.c','net/ipv4/fib_frontend.c','net/ipv4/fib_rules.c','include/net/flow.h']:
 r=subprocess.run(['wsl.exe','-d','Ubuntu','--','cat','/root/t110-build/kernel-display-i2c/'+f],capture_output=True,timeout=45)
 assert r.returncode==0,r.stderr.decode(errors='replace')
 (e/('source-'+f.replace('/','_'))).write_bytes(r.stdout);print(f,len(r.stdout))
