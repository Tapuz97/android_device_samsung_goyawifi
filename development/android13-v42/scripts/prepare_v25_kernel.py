"""Adapt Binder security-context transactions to the existing 3.4 Binder backport."""
from pathlib import Path
import difflib, json, hashlib, re
base=Path('/root/t110-build')
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
source=base/'kernel-alarm'
target=base/'kernel-binder-secctx'
patch=[]

def replace(s,old,new):
    assert s.count(old)==1,old[:100]
    return s.replace(old,new)

name='drivers/staging/android/uapi/binder.h'
old=(source/name).read_text(); s=old
s=replace(s,'FLAT_BINDER_FLAG_ACCEPTS_FDS = 0x100,','FLAT_BINDER_FLAG_ACCEPTS_FDS = 0x100,\n\tFLAT_BINDER_FLAG_TXN_SECURITY_CTX = 0x1000,')
s=replace(s,'struct binder_transaction_data_sg {','struct binder_transaction_data_secctx {\n\tstruct binder_transaction_data transaction_data;\n\tbinder_uintptr_t secctx;\n};\n\nstruct binder_transaction_data_sg {')
s=replace(s,"\tBR_TRANSACTION = _IOR('r', 2, struct binder_transaction_data),","\tBR_TRANSACTION_SEC_CTX = _IOR('r', 2, struct binder_transaction_data_secctx),\n\tBR_TRANSACTION = _IOR('r', 2, struct binder_transaction_data),")
(target/name).write_text(s)
patch.extend(difflib.unified_diff(old.splitlines(True),s.splitlines(True),'a/'+name,'b/'+name))

name='drivers/staging/android/binder.c'
old=(source/name).read_text(); s=old
s=replace(s,'\tunsigned accept_fds:1;','\tunsigned accept_fds:1;\n\tunsigned txn_security_ctx:1;')
s=replace(s,'\tstruct task_struct *tsk;','\tstruct task_struct *tsk;\n\t/* Immutable SID of the credentials which opened this Binder fd. */\n\tu32 opener_sid;')
s=replace(s,'\tuid_t\tsender_euid;','\tuid_t\tsender_euid;\n\tbinder_uintptr_t security_ctx;')
s=replace(s,'\tproc->tsk = current->group_leader;','\tproc->tsk = current->group_leader;\n\tsecurity_task_getsecid(current, &proc->opener_sid);')
s=replace(s,'\t\tnode->accept_fds = !!(fp->flags & FLAT_BINDER_FLAG_ACCEPTS_FDS);','\t\tnode->accept_fds = !!(fp->flags & FLAT_BINDER_FLAG_ACCEPTS_FDS);\n\t\tnode->txn_security_ctx = !!(fp->flags & FLAT_BINDER_FLAG_TXN_SECURITY_CTX);')
s=replace(s,'\tbinder_size_t last_fixup_min_off = 0;','\tbinder_size_t last_fixup_min_off = 0;\n\tchar *secctx = NULL;\n\tu32 secctx_sz = 0;\n\tbinder_size_t secctx_space = 0;')
anchor='\ttrace_binder_transaction(reply, t, target_node);'
s=replace(s,anchor,'''\t/* Reserve a kernel-owned tail after the caller's scatter/gather area.
\t * Never derive this identity from userspace or a reused task PID.
\t */
\tif (target_node && target_node->txn_security_ctx) {
\t\tret = security_secid_to_secctx(proc->opener_sid, &secctx, &secctx_sz);
\t\tif (ret < 0 || !secctx || !secctx_sz || secctx[secctx_sz - 1]) {
\t\t\treturn_error = BR_FAILED_REPLY;
\t\t\tgoto err_binder_alloc_buf_failed;
\t\t}
\t\tsecctx_space = ALIGN(secctx_sz, sizeof(u64));
\t\tif (secctx_space < secctx_sz ||
\t\t    extra_buffers_size > (binder_size_t)-1 - secctx_space) {
\t\t\treturn_error = BR_FAILED_REPLY;
\t\t\tgoto err_binder_alloc_buf_failed;
\t\t}
\t\textra_buffers_size += secctx_space;
\t}

'''+anchor)
anchor='\tt->buffer->allow_user_free = 0;'
s=replace(s,anchor,'''\tif (secctx) {
\t\tsize_t ctx_offset = ALIGN(tr->data_size, sizeof(void *)) +
\t\t\tALIGN(tr->offsets_size, sizeof(void *)) +
\t\t\textra_buffers_size - secctx_space;
\t\tu8 *ctx = (u8 *)t->buffer->data + ctx_offset;

\t\tmemset(ctx, 0, secctx_space);
\t\tmemcpy(ctx, secctx, secctx_sz);
\t\tt->security_ctx = (binder_uintptr_t)((uintptr_t)ctx +
\t\t\ttarget_proc->user_buffer_offset);
\t\tsecurity_release_secctx(secctx, secctx_sz);
\t\tsecctx = NULL;
\t}
'''+anchor)
s=replace(s,'\tsg_buf_end = sg_bufp + extra_buffers_size;','\t/* Sender-controlled SG objects cannot overwrite the security label. */\n\tsg_buf_end = sg_bufp + extra_buffers_size - secctx_space;')
s=replace(s,'err_binder_alloc_buf_failed:\n\tkfree(tcomplete);','err_binder_alloc_buf_failed:\n\tif (secctx)\n\t\tsecurity_release_secctx(secctx, secctx_sz);\n\tkfree(tcomplete);')
# Change only the reader, preserving plain transaction/reply ABI for legacy nodes.
start=s.index('static int binder_thread_read('); end=s.index('\nstatic ',start+1)
body=s[start:end]
body=replace(body,'\t\tstruct binder_transaction_data tr;','\t\tstruct binder_transaction_data_secctx tr;\n\t\tstruct binder_transaction_data *trd = &tr.transaction_data;\n\t\tsize_t trsize = sizeof(*trd);')
body=re.sub(r'\btr\.', 'trd->', body).replace('&trd->transaction_data', '&tr.transaction_data')
body=replace(body,'if (end - ptr < sizeof(tr) + 4)','if (end - ptr < sizeof(*trd) + 4)')
body=replace(body,'\t\tBUG_ON(t->buffer == NULL);','\t\tif (t->security_ctx && end - ptr < sizeof(tr) + 4)\n\t\t\tbreak;\n\n\t\tBUG_ON(t->buffer == NULL);')
body=replace(body,'\t\tif (put_user(cmd, (uint32_t __user *)ptr))\n\t\t\treturn -EFAULT;\n\t\tptr += sizeof(uint32_t);\n\t\tif (copy_to_user(ptr, &tr, sizeof(tr)))',
'''\t\ttr.secctx = t->security_ctx;
\t\tif (t->security_ctx) {
\t\t\tcmd = BR_TRANSACTION_SEC_CTX;
\t\t\ttrsize = sizeof(tr);
\t\t}
\t\tif (put_user(cmd, (uint32_t __user *)ptr))
\t\t\treturn -EFAULT;
\t\tptr += sizeof(uint32_t);
\t\tif (copy_to_user(ptr, &tr, trsize))''')
body=replace(body,'\t\tptr += sizeof(tr);','\t\tptr += trsize;')
body=replace(body,'if (cmd == BR_TRANSACTION && !(t->flags & TF_ONE_WAY))','if (cmd != BR_REPLY && !(t->flags & TF_ONE_WAY))')
s=s[:start]+body+s[end:]
(target/name).write_text(s)
patch.extend(difflib.unified_diff(old.splitlines(True),s.splitlines(True),'a/'+name,'b/'+name))
(project/'patches/0044-kernel-binder-security-context.patch').write_text(''.join(patch))
e=project/'evidence/offline-v25'; e.mkdir(exist_ok=True)
(e/'kernel-adaptation.json').write_text(json.dumps(dict(
    parent='kernel-alarm',target='kernel-binder-secctx',
    identity='SELinux SID captured from current credentials at binder_open; never a userspace PID lookup',
    upstream=['ec74136ded79','4d5b5539742d2554591751b4248b0204d20dcc9d'],
    no_boot_tests=True,hardware_validated=False),indent=2)+'\n')
print('Prepared Binder SEC_CTX backport; compile and checks pending')
