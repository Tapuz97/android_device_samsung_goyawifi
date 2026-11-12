"""Replay the real Android ARM compiler invocation on both changed source files."""
from pathlib import Path
import shlex, subprocess
base=Path('/root/t110-build')
root=base/'lineage20'
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
log=(base/'logs/system-image-20261106T173909Z.log').read_text()
command=next(line for line in log.splitlines() if line.startswith('PWD=/proc/self/cwd ') and
             'gl/GLESRenderEngine.cpp' in line)
args=shlex.split(command)[1:]
# Avoid writing build outputs or dependency files in this standalone check.
for flag in ['-o','-MF']:
    if flag in args:
        index=args.index(flag)
        del args[index:index+2]
args=[a for a in args if a not in ('-c','-MD','-MMD')]
args.append('-fsyntax-only')
old='frameworks/native/libs/renderengine/gl/GLESRenderEngine.cpp'
report=[]
for name in ['GLESRenderEngine.cpp','T110EglWindow.cpp']:
    cmd=[a.replace(old,'frameworks/native/libs/renderengine/gl/'+name) for a in args]
    result=subprocess.run(cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    report.append(name+' exit='+str(result.returncode)+'\n'+result.stdout)
    print(report[-1],flush=True)
    if result.returncode:
        (project/'evidence/offline-v23/arm-graphics-compile.log').write_text('\n'.join(report))
        raise SystemExit(result.returncode)
(project/'evidence/offline-v23/arm-graphics-compile.log').write_text('\n'.join(report))
