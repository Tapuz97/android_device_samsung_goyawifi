from pathlib import Path
import subprocess,struct,json,hashlib
base=Path('/root/t110-build');root=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
d=base/'binder-abi-probe';d.mkdir(exist_ok=True)
headers={'legacy':base/'kernel-binder/drivers/staging/android/binder.h','android13_32bit':root/'evidence/los20-binder-header.txt'}
expressions=['sizeof(struct binder_write_read)','sizeof(struct binder_transaction_data)','sizeof(struct flat_binder_object)','sizeof(struct binder_version)','BINDER_WRITE_READ','BINDER_SET_CONTEXT_MGR','BINDER_VERSION','BC_TRANSACTION','BC_REPLY','BR_TRANSACTION','BR_REPLY','BC_FREE_BUFFER','BR_FAILED_REPLY','__builtin_offsetof(struct binder_transaction_data,data)']
records={}
for name,header in headers.items():
 c=d/(name+'.c');c.write_text('#include <stdint.h>\n#include <sys/types.h>\n#define BINDER_IPC_32BIT 1\n#include "'+str(header)+'"\nconst unsigned int abi[] = {'+','.join(expressions)+'};\n')
 obj=d/(name+'.o');out=d/(name+'.bin')
 subprocess.run(['arm-linux-gnueabi-gcc','-c',str(c),'-o',str(obj)],check=True)
 subprocess.run(['arm-linux-gnueabi-objcopy','-O','binary','-j','.rodata',str(obj),str(out)],check=True)
 values=struct.unpack('<'+'I'*len(expressions),out.read_bytes());records[name]=dict(zip(expressions,values))
assert records['legacy']==records['android13_32bit'],records
report={'status':'PASS: overlapping base ABI matches when Android 13 is compiled BINDER_IPC_32BIT','records':records,'not_covered':['Scatter-gather transaction commands','Binder PTR/FDA objects','Multiple Binder contexts','Transaction security contexts','Modern libbinder runtime'],'header_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in headers.items()}}
(root/'evidence/binder-base-abi-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['status']);print(json.dumps(records['legacy'],indent=2))