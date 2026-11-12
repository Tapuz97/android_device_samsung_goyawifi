from pathlib import Path
import shlex,subprocess
base=Path('/root/t110-build');out=base/'out-qemu-binder-modern'
line=(out/'drivers/staging/android/.binder.o.cmd').read_text().splitlines()[0].split(' := ',1)[1]
args=shlex.split(line);args=[a for a in args if a!='-w'];args.append('-Werror')
args[args.index('-o')+1]=str(base/'binder-strict-check.o')
args=[('-Wp,-MD,'+str(base/'binder-strict-check.d')) if a.startswith('-Wp,-MD,') else a for a in args]
r=subprocess.run(args,cwd=out,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(base/'logs/binder-strict-check.log').write_text(r.stdout)
print(r.stdout);print('Strict Binder compile exit:',r.returncode)
raise SystemExit(r.returncode)