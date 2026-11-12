"""Find stock graphics imports lost when using the built Android 13 core libraries."""
import functools
import json
from pathlib import Path
import re
import subprocess

project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
stock = Path('/root/t110-build/stock-system-files/lib')
modern = [project/'artifacts/android13-hwbinder/bundle/lib', project/'artifacts/android13-native/bundle/lib']
roots = ['hw/hwcomposer.mrvl.so', 'hw/gralloc.mrvl.so', 'libHWComposerGC.so', 'libGAL.so']

@functools.cache
def elf(path):
    output = subprocess.check_output(['readelf', '--wide', '--dynamic', '--dyn-syms', str(path)],
                                     text=True, stderr=subprocess.DEVNULL)
    needed = re.findall(r'Shared library: \[(.*?)\]', output)
    imports, exports = set(), set()
    for line in output.splitlines():
        fields = line.split()
        if len(fields) < 8 or not re.fullmatch(r'\d+:', fields[0]):
            continue
        if re.fullmatch(r'\(\d+\)', fields[-1]):
            fields.pop()
        binding, visibility, section, name = fields[-4:]
        if section == 'UND' and binding == 'GLOBAL':
            imports.add(name)
        elif section != 'UND' and binding in ('GLOBAL', 'WEAK') and visibility in ('DEFAULT', 'PROTECTED'):
            exports.add(name.replace('@@', '@'))
            if '@@' in name:
                exports.add(name.split('@@', 1)[0])
    return needed, imports, exports

def closure(overlays):
    found, missing = {}, set()
    pending = list(roots)
    while pending:
        name = pending.pop()
        if name in found or name in missing:
            continue
        path = next((directory/name for directory in modern if overlays and (directory/name).is_file()), stock/name)
        if not path.is_file():
            missing.add(name)
            continue
        needed, imports, exports = elf(path)
        found[name] = {'origin': 'stock' if path.is_relative_to(stock) else 'android13',
                       'imports': imports, 'exports': exports}
        pending.extend(needed)
    return found, missing

baseline, baseline_missing = closure(False)
overlay, overlay_missing = closure(True)
stock_exports = set().union(*(entry['exports'] for entry in baseline.values()))
overlay_exports = set().union(*(entry['exports'] for entry in overlay.values()))
lost = {name: sorted(entry['imports'] & (stock_exports - overlay_exports))
        for name, entry in overlay.items() if entry['origin'] == 'stock'}
lost = {name: symbols for name, symbols in lost.items() if symbols}
providers = {symbol: sorted(name for name, entry in baseline.items() if symbol in entry['exports'])
             for symbol in sorted(set().union(*lost.values()))}
report = {
    'roots': roots,
    'android13_overlays': sorted(name for name, entry in overlay.items() if entry['origin'] == 'android13'),
    'unavailable_stock_dependencies': sorted(baseline_missing),
    'unavailable_overlay_dependencies': sorted(overlay_missing),
    'stock_imports_lost_after_overlay': lost,
    'old_providers': providers,
    'scope': 'Static ELF export comparison across the available dependency closure. Runtime visibility, C++ object layouts, buffer ABI and remaining platform libraries require separate validation.'
}
(project/'evidence/graphics-legacy-symbol-gaps.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'closure_libraries': len(overlay), 'stock_consumers_with_missing_exports': len(lost),
                  'lost_export_count': len(providers), 'missing_dependencies': sorted(overlay_missing)}, indent=2))
