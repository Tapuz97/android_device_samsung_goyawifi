from pathlib import Path
import argparse,hashlib,json,os,struct
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');b=Path('/root/t110-build');e=p/'evidence/hardware-bt-sd';product=b/'out-system/target/product/t110_bringup'
parser=argparse.ArgumentParser();parser.add_argument('--compiled-log');args=parser.parse_args()
log=b/'logs'/args.compiled_log if args.compiled_log else Path((e/'build-log.txt').read_text().strip())
text=log.read_text(errors='replace');whole_build_passed='build completed successfully' in text
assert whole_build_passed or (args.compiled_log and 'Install: '+str(product/'data/nativetest/bluetooth-vendor-interface-unit-tests/bluetooth-vendor-interface-unit-tests') in text)
matches=[f for f in (product/'data').glob('nativetest*/**/bluetooth-vendor-interface-unit-tests') if f.is_file()];assert len(matches)==1,matches
binary=matches[0].read_bytes();assert binary[:6]==b'\x7fELF\x01\x01' and struct.unpack_from('<H',binary,18)[0]==40
for name,expected in json.loads((e/'h4-production-source.json').read_text())['files'].items():assert hashlib.sha256((b/'lineage20/hardware/interfaces'/name).read_bytes()).hexdigest()==expected,name
(e/'bluetooth-vendor-interface-unit-tests').write_bytes(binary)
(e/'h4-unit-build.json').write_text(json.dumps(dict(sha256=hashlib.sha256(binary).hexdigest(),source=str(matches[0]),build_log=str(log),whole_rom_build_passed=whole_build_passed),indent=2)+'\n');print('H4_PRODUCTION_TESTS_COMPILED')
