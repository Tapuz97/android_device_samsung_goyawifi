"""Create a reviewable Linux3.4 UID-routing backport; never flash the tablet.

Protocol/cache changes derive from pinned Android hammerhead Linux3.4 source;
FRA_UID_RANGE and RTA_UID use modern upstream ABI, not legacy Android IDs.
"""
from pathlib import Path
import difflib,hashlib,json,re,subprocess

p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
src=Path('/root/t110-build/kernel-display-i2c')
work=Path('/root/t110-build/uid-routing-backport')
refs=p/'evidence/hardware-v35/uid-upstream'
manifest_path=p/'evidence/hardware-v35/uid-source.json'
prior=json.loads(manifest_path.read_text()) if manifest_path.exists() else {'files':[]}
known={item['path']:{item['before_sha256'],item['after_sha256']} for item in prior['files']}
allowed_current={}
paths=set()
for name in ('legacy-uid.patch','inet-uid.patch','sock-uid.patch'):
    paths.update(re.findall(r'^diff --git a/(\S+)',(refs/name).read_text(),re.M))
paths={f.replace('include/uapi/','include/') for f in paths}
texts={};original={}
for name in sorted(paths):
    f=src/name;ref=refs/('hammerhead-'+name.replace('/','_'))
    if not f.is_file() or not ref.is_file():continue
    digest=hashlib.sha256(f.read_bytes()).hexdigest()
    if name in known:assert digest in known[name], 'Unreviewed source edit: '+name
    allowed_current[name]=digest
    saved=work/'base'/name
    before=saved.read_text() if saved.exists() else f.read_text()
    original[name]=before
    old=before.splitlines(True);new=ref.read_text().splitlines(True);lines=[]
    for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
        changed=''.join(old[a:b])+''.join(new[c:d])
        # Include only the UID change itself, not unrelated changes in its hunk.
        lines.extend(new[c:d] if tag!='equal' and re.search('uid',changed,re.I) else old[a:b])
    texts[name]=''.join(lines)
def change(name,old,new,count=1):
    assert texts[name].count(old)==count,(name,old[:100],texts[name].count(old))
    texts[name]=texts[name].replace(old,new)

# Reuse the legacy implementation internally, exposing upstream wire attributes.
change('include/linux/fib_rules.h','\tFRA_UID_START,\t/* UID range */\n\tFRA_UID_END,',
       '\tFRA_PAD,\n\tFRA_L3MDEV,\t/* Reserved: not implemented on this kernel. */\n\tFRA_UID_RANGE,\t/* Modern ABI: attribute20, two native-endian u32s. */')
change('include/linux/fib_rules.h','enum {\n\tFRA_UNSPEC,',
       'struct fib_rule_uid_range {\n\t__u32 start;\n\t__u32 end;\n};\n\nenum {\n\tFRA_UNSPEC,')
change('include/linux/rtnetlink.h','\tRTA_MFC_STATS, /* not used - backported from the future */\n\tRTA_UID,',
       '\t/* Values17..24 are reserved for upstream route attributes. */\n\tRTA_UID = 25,')
change('include/net/fib_rules.h','\t[FRA_UID_START]\t= { .type = NLA_U32 }, \\\n\t[FRA_UID_END]\t= { .type = NLA_U32 }',
       '\t[FRA_UID_RANGE]\t= { .len = sizeof(struct fib_rule_uid_range) }')
name='net/core/fib_rules.c'
start=texts[name].index('static inline uid_t fib_nl_uid(')
end=texts[name].index('static int fib_uid_range_match',start)
texts[name]=texts[name][:start]+texts[name][end:]
start=texts[name].index('\t/* UID start and end must either both be valid or both unspecified. */')
end=texts[name].index('\n\terr = ops->configure',start)
texts[name]=texts[name][:start]+'''\t/* Keep per-app selectors; never accept them as wildcard rules. */
\trule->uid_start = rule->uid_end = INVALID_UID;
\tif (tb[FRA_L3MDEV]) {
\t\terr = -EOPNOTSUPP;
\t\tgoto errout_free;
\t}
\tif (tb[FRA_UID_RANGE]) {
\t\tconst struct fib_rule_uid_range *range;
\t\terr = -EINVAL;
\t\tif (nla_len(tb[FRA_UID_RANGE]) != sizeof(*range))
\t\t\tgoto errout_free;
\t\trange = nla_data(tb[FRA_UID_RANGE]);
\t\tif (!uid_valid(range->start) || !uid_valid(range->end) ||
\t\t    range->start > range->end)
\t\t\tgoto errout_free;
\t\trule->uid_start = range->start;
\t\trule->uid_end = range->end;
\t}
'''+texts[name][end:]
start=texts[name].index('\t\tif (tb[FRA_UID_START]')
end=texts[name].index('\n\t\tif (!ops->compare',start)
texts[name]=texts[name][:start]+'''\t\tif (tb[FRA_UID_RANGE]) {
\t\t\tconst struct fib_rule_uid_range *range;
\t\t\tif (nla_len(tb[FRA_UID_RANGE]) != sizeof(*range)) {
\t\t\t\terr = -EINVAL;
\t\t\t\tgoto errout;
\t\t\t}
\t\t\trange = nla_data(tb[FRA_UID_RANGE]);
\t\t\tif (rule->uid_start != range->start || rule->uid_end != range->end)
\t\t\t\tcontinue;
\t\t}
'''+texts[name][end:]
change(name,'\t\t\t + nla_total_size(4) /* FRA_UID_START */\n\t\t\t + nla_total_size(4); /* FRA_UID_END */',
       '\t\t\t + nla_total_size(sizeof(struct fib_rule_uid_range));')
start=texts[name].index('\tif (uid_valid(rule->uid_start))')
end=texts[name].index('\n\tif (ops->fill',start)
texts[name]=texts[name][:start]+'''\tif (uid_valid(rule->uid_start)) {
\t\tstruct fib_rule_uid_range range = { rule->uid_start, rule->uid_end };
\t\tNLA_PUT(skb, FRA_UID_RANGE, sizeof(range), &range);
\t}
'''+texts[name][end:]

# The retained route UID must follow the socket even after close(), accept(),
# or fchown(); the old callback-based sock_i_uid returns0 after orphaning.
name='include/net/sock.h'
change(name,'\t__u32\t\t\tsk_mark;','\t__u32\t\t\tsk_mark;\n\tuid_t\t\t\tsk_uid;')
change(name,'\tsk_set_socket(sk, parent);','\tsk_set_socket(sk, parent);\n\tsk->sk_uid = SOCK_INODE(parent)->i_uid;')
change(name,'extern int sock_i_uid(struct sock *sk);','extern int sock_i_uid(struct sock *sk);\n\nstatic inline uid_t sock_net_uid(const struct net *net, const struct sock *sk)\n{\n\treturn sk ? sk->sk_uid : 0;\n}\n')
name='net/core/sock.c'
change(name,'\t\tsock->sk\t=\tsk;\n\t} else\n\t\tsk->sk_wq\t=\tNULL;',
       '\t\tsock->sk\t=\tsk;\n\t\tsk->sk_uid\t=\tSOCK_INODE(sock)->i_uid;\n\t} else {\n\t\tsk->sk_wq\t=\tNULL;\n\t\tsk->sk_uid\t=\t0;\n\t}')
start=texts[name].index('int sock_i_uid(struct sock *sk)\n{')
end=texts[name].index('\nEXPORT_SYMBOL(sock_i_uid);',start)
texts[name]=texts[name][:start]+'''int sock_i_uid(struct sock *sk)
{
\treturn ACCESS_ONCE(sk->sk_uid);
}'''+texts[name][end:]
name='net/socket.c'
insert='''static int sockfs_setattr(struct dentry *dentry, struct iattr *attr)
{
\tint err = simple_setattr(dentry, attr);
\tstruct socket *sock = SOCKET_I(dentry->d_inode);

\tif (!err && (attr->ia_valid & ATTR_UID) && sock->sk) {
\t\twrite_lock_bh(&sock->sk->sk_callback_lock);
\t\tsock->sk->sk_uid = dentry->d_inode->i_uid;
\t\twrite_unlock_bh(&sock->sk->sk_callback_lock);
\t}
\treturn err;
}

static const struct inode_operations sockfs_inode_ops = {
\t.setattr = sockfs_setattr,
};

'''
change(name,'static struct socket *sock_alloc(void)\n{',insert+'static struct socket *sock_alloc(void)\n{')
change(name,'\tinode->i_gid = current_fsgid();','\tinode->i_gid = current_fsgid();\n\tinode->i_op = &sockfs_inode_ops;')

# The 3.4 source uses plain uid_t and cannot represent user namespaces. Avoid
# implying that a future USER_NS-enabled configuration has been qualified.
change('include/net/flow.h','#include <linux/atomic.h>',
       '#include <linux/atomic.h>\n#ifdef CONFIG_USER_NS\n#error "UID routing backport requires a user-namespace-aware UID conversion port"\n#endif')

# This vendor3.4 IPv6 path predates the loopback-iif convention used by netd.
# Apply it only to output; forwarded/input packets retain their actual iif.
change('net/ipv6/route.c','\tint flags = 0;\n\n\tif ((sk && sk->sk_bound_dev_if)',
       '\tint flags = 0;\n\n\tfl6->flowi6_iif = net->loopback_dev->ifindex;\n\tif ((sk && sk->sk_bound_dev_if)')
change('net/ipv4/fib_frontend.c','\tfl4.flowi4_iif = oif;',
       '\tfl4.flowi4_iif = oif;\n\tfl4.flowi4_uid = (uid_t)-1;')
change('net/ipv4/route.c','\tfl4.flowi4_iif = dev->ifindex;',
       '\tfl4.flowi4_iif = dev->ifindex;\n\tfl4.flowi4_uid = (uid_t)-1;')

diff=[];records=[]
for name,after in sorted(texts.items()):
    before=original[name]
    if after==before:continue
    base=work/'base'/name;base.parent.mkdir(parents=True,exist_ok=True)
    if base.exists():assert base.read_text()==before
    else:base.write_text(before)
    candidate=work/'candidate'/name;candidate.parent.mkdir(parents=True,exist_ok=True);candidate.write_text(after)
    diff.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    records.append(dict(path=name,before_sha256=hashlib.sha256(before.encode()).hexdigest(),after_sha256=hashlib.sha256(after.encode()).hexdigest()))
patch=''.join(diff)
(work/'candidate.patch').write_text(patch)
(p/'patches/0095-kernel-modern-uid-routing.patch').write_text(patch)
subprocess.run(['patch','--dry-run','-p1','-i',str(work/'candidate.patch')],cwd=work/'base',check=True)
(p/'evidence/hardware-v35/uid-source.json').write_text(json.dumps(dict(status='CANDIDATE_NOT_APPLIED_OR_BUILT',files=records,allowed_current_hashes=allowed_current),indent=2)+'\n')
print('UID_CANDIDATE_STAGED',len(records),'files',len(patch),'bytes')
