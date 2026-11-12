"""Query the compiled Android policy in host libsepol, without loading a kernel policy."""
import argparse
import ctypes as c
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('policy',type=Path)
parser.add_argument('--report',required=True,type=Path)
parser.add_argument('--baseline',action='store_true')
args=parser.parse_args()
lib=c.CDLL('libsepol.so.2')
libc=c.CDLL(None)
libc.fopen.argtypes=[c.c_char_p,c.c_char_p]
libc.fopen.restype=c.c_void_p
libc.fclose.argtypes=[c.c_void_p]
lib.sepol_set_policydb_from_file.argtypes=[c.c_void_p]
lib.sepol_context_to_sid.argtypes=[c.c_char_p,c.c_size_t,c.POINTER(c.c_uint32)]
lib.sepol_string_to_security_class.argtypes=[c.c_char_p,c.POINTER(c.c_uint16)]
lib.sepol_string_to_av_perm.argtypes=[c.c_uint16,c.c_char_p,c.POINTER(c.c_uint32)]
lib.sepol_compute_av.argtypes=[c.c_uint32,c.c_uint32,c.c_uint16,c.c_uint32,c.c_void_p]
fp=libc.fopen(str(args.policy).encode(),b'rb')
assert fp
try:
    assert lib.sepol_set_policydb_from_file(fp)==0
finally:
    libc.fclose(fp)

def sid(context):
    value=c.c_uint32()
    encoded=context.encode()
    assert lib.sepol_context_to_sid(encoded,len(encoded)+1,c.byref(value))==0,context
    return value

tclass=c.c_uint16()
assert lib.sepol_string_to_security_class(b'chr_file',c.byref(tclass))==0
rows=[]
for domain in ['platform_app','untrusted_app','system_server','mediacodec','isolated_app']:
    for target in ['gpu_device','ion_device']:
        permissions={}
        source_context=f'u:r:{domain}:s0'
        for name in ['open','read','write','ioctl','map']:
            bit=c.c_uint32()
            assert lib.sepol_string_to_av_perm(tclass,name.encode(),c.byref(bit))==0
            decision=c.create_string_buffer(64) # allowed is the first uint32 field
            assert lib.sepol_compute_av(sid(source_context),sid(f'u:object_r:{target}:s0'),
                tclass,bit,decision)==0
            permissions[name]=bool(c.cast(decision,c.POINTER(c.c_uint32))[0]&bit.value)
        rows.append(dict(domain=domain,target=target,permissions=permissions))

indexed={(row['domain'],row['target']):row['permissions'] for row in rows}
for domain in ['platform_app','untrusted_app','system_server']:
    assert indexed[domain,'ion_device']['read']
    assert indexed[domain,'ion_device']['write'] != args.baseline
for domain in ['platform_app','untrusted_app']:
    assert all(indexed[domain,'gpu_device'].values())
assert indexed['mediacodec','ion_device']['read']
assert not indexed['isolated_app','ion_device']['write']
assert not indexed['isolated_app','gpu_device']['write']
report=dict(status='PASS',baseline=args.baseline,checks=rows,kernel_policy_loaded=False)
args.report.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
