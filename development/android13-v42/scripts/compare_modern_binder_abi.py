from pathlib import Path
import subprocess,struct,json,hashlib
base=Path('/root/t110-build');root=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
d=base/'binder-modern-abi-probe';d.mkdir(exist_ok=True)
headers={'ported_driver':base/'kernel-binder-modern/drivers/staging/android/uapi/binder.h','android13_32bit':root/'evidence/los20-binder-header.txt'}
expressions=['sizeof(struct binder_write_read)','sizeof(struct binder_transaction_data)','sizeof(struct flat_binder_object)','sizeof(struct binder_version)','BINDER_WRITE_READ','BINDER_SET_CONTEXT_MGR','BINDER_VERSION','BC_TRANSACTION','BC_REPLY','BR_TRANSACTION','BR_REPLY','BC_FREE_BUFFER','BR_FAILED_REPLY','__builtin_offsetof(struct binder_transaction_data,data)']
expressions += ['sizeof(struct binder_transaction_data_sg)','sizeof(struct binder_buffer_object)','sizeof(struct binder_fd_array_object)','sizeof(struct binder_fd_object)','BC_TRANSACTION_SG','BC_REPLY_SG','BINDER_TYPE_PTR','BINDER_TYPE_FDA','__builtin_offsetof(struct binder_buffer_object,parent_offset)','__builtin_offsetof(struct binder_transaction_data_sg,buffers_size)']
records={}
for name,header in headers.items():
 c=d/(name+'.c');c.write_text('#include <stdint.h>\n#include <linux/types.h>\n#include <sys/types.h>\n#define BINDER_IPC_32BIT 1\n#include "'+str(header)+'"\nconst unsigned int abi[] = {'+','.join(expressions)+'};\n')
 obj=d/(name+'.o');out=d/(name+'.bin')
 subprocess.run(['arm-linux-gnueabi-gcc','-c',str(c),'-o',str(obj)],check=True)
 subprocess.run(['arm-linux-gnueabi-objcopy','-O','binary','-j','.rodata',str(obj),str(out)],check=True)
 values=struct.unpack('<'+'I'*len(expressions),out.read_bytes());records[name]=dict(zip(expressions,values))
assert records['ported_driver']==records['android13_32bit'],records
report={'status':'PASS: base and scatter-gather ABI match when Android 13 is compiled BINDER_IPC_32BIT','records':records,'not_covered':['Transaction security contexts','Modern libbinder/libhwbinder runtime'],'header_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in headers.items()}}
(root/'evidence/binder-modern-abi-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['status']);print(json.dumps(records['ported_driver'],indent=2))