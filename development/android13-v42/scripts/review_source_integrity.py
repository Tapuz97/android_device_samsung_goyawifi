"""Classify audit differences using Git checkout filters and our saved patches."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import shutil

assert os.environ.get('WSL_DISTRO_NAME') == 'T110Build'
root = Path('/root/t110-build/lineage20')
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
evidence = project / 'evidence'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--after-enclosure', action='store_true')
args = parser.parse_args()
label = 'after-enclosure' if args.after_enclosure else 'after-cable'
audit = json.loads((evidence / f'source-integrity-{label}.json').read_text())
assert audit['projects'] == len((root / '.repo/project.list').read_text().splitlines())
assert not audit['failed_projects'], 'Git object or file read failures'
patches = {
    'build/soong': ('0014-host-soong-gc-opt-in.patch', {'ui/build/soong.go'}),
    'system/core': ('0009-android13-t110-legacy-processgroups.patch', {'libprocessgroup/processgroup.cpp'}),
    'packages/modules/adb': ('0013-adbd-t110-synchronous-functionfs.patch', {'daemon/usb.cpp'}),
}
result = {'projects': audit['projects'], 'files': audit['files'], 'bytes': audit['bytes'],
          'git_filter_equivalent': [], 'approved_patch_changes': [], 'unexpected_changes': []}
for entry in audit['changed_projects']:
    relative = entry['project']
    repo = root / relative
    if relative in patches:
        patch_name, allowed = patches[relative]
        patch_file = project / 'patches' / patch_name
        subprocess.run(['git', '-C', str(repo), 'apply', '--reverse', '--check', str(patch_file)], check=True)
        # Reverse the patch in an isolated scratch copy, then require the entire
        # resulting tracked file to match Git. This rejects unrelated edits.
        exact_files = set()
        with tempfile.TemporaryDirectory(prefix='t110-patch-review-') as temporary:
            tmp = Path(temporary)
            for line in patch_file.read_text().splitlines():
                if line.startswith('+++ b/'):
                    name = line[6:]
                    assert not Path(name).is_absolute() and '..' not in Path(name).parts
                    target = tmp / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(repo / name, target)
            subprocess.run(['git', 'apply', '--reverse', str(patch_file)], cwd=tmp, check=True)
            for change in entry['changes']:
                name = change['path']
                if name in allowed:
                    reversed_hash = subprocess.check_output(['git', '-C', str(repo), 'hash-object', '--path='+name, str(tmp/name)], text=True).strip()
                    if reversed_hash == change['expected']:
                        exact_files.add(name)
    for change in entry['changes']:
        name = change['path']
        normalized = subprocess.check_output(['git', '-C', str(repo), 'hash-object', '--path='+name, name], text=True).strip()
        item = {'project': relative, 'path': name}
        if normalized == change['expected']:
            result['git_filter_equivalent'].append(item)
        elif relative in patches and name in patches[relative][1]:
            patch_file = project / 'patches' / patches[relative][0]
            exact = name in exact_files
            item['exact_patch_match'] = exact
            item['patch_sha256'] = hashlib.sha256(patch_file.read_bytes()).hexdigest()
            result['approved_patch_changes' if exact else 'unexpected_changes'].append(item)
        else:
            result['unexpected_changes'].append(item)
result['pass'] = not result['unexpected_changes']
(evidence / ('source-integrity-review-after-enclosure.json' if args.after_enclosure else 'source-integrity-review.json')).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: len(v) if isinstance(v, list) else v for k, v in result.items()}, indent=2))
assert result['pass'], 'Unexpected working-tree differences require inspection'
