"""Inspect the existing ART pipeline without changing source or starting a build."""
from pathlib import Path
import subprocess
root = Path('/root/t110-build')
r = subprocess.run([str(root/'out-system/host/linux-x86/bin/dexpreopt_gen'), '-help'], capture_output=True, text=True)
print((r.stdout+r.stderr)[:4500])
print('CONFIGS')
print('\n'.join(str(x) for x in (root/'out-system/soong').glob('*dexpreopt*')))
p = root/'lineage20/build/soong/dexpreopt/dexpreopt_gen/dexpreopt_gen.go'
for i, line in enumerate(p.read_text().splitlines()):
    if any(k in line for k in ['flag.', 'moduleConfig.', 'dexLocation', 'DexPath', 'BuildPath', 'scriptPath']):
        print(f'{i+1}: {line}')
