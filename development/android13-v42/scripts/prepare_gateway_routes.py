"""Backport the explicit-table nexthop lookup from mainline v4.3 to 3.4.
Only kernel control-plane gateway validation changes; packet UID rules remain.
"""
from pathlib import Path
import difflib,hashlib,json
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/hardware-v35'
src=Path('/root/t110-build/kernel-display-i2c/net/ipv4/fib_semantics.c')
before=(e/'source-net_ipv4_fib_semantics.c').read_text()
after=before.replace('''		{
			struct flowi4 fl4 = {
				.daddr = nh->nh_gw,''','''		{
			struct fib_table *tbl = NULL;
			struct flowi4 fl4 = {
				.daddr = nh->nh_gw,''',1)
old='''				.flowi4_oif = nh->nh_oif,
			};'''
new='''				.flowi4_oif = nh->nh_oif,
				.flowi4_iif = net->loopback_dev->ifindex,
				/* Gateway validation has no packet/socket owner. */
				.flowi4_uid = (uid_t)-1,
			};'''
assert after.count(old)==1;after=after.replace(old,new,1)
old='\t\t\terr = fib_lookup(net, &fl4, &res);'
new='''			/* Prefer the route's own table before policy lookup. Android
			 * keeps each network's connected prefix in a separate table.
			 * Mainline v4.3 fib_check_nh uses the same lookup order. */
			if (cfg->fc_table)
				tbl = fib_get_table(net, cfg->fc_table);
			if (tbl)
				err = fib_table_lookup(tbl, &fl4, &res, FIB_LOOKUP_NOREF);
			if (!tbl || err)
				err = fib_lookup(net, &fl4, &res);'''
assert after.count(old)==1;after=after.replace(old,new,1)
assert before!=after
prior=after.replace('.flowi4_iif = net->loopback_dev->ifindex,','.flowi4_iif = LOOPBACK_IFINDEX,')
assert src.read_text() in (before,prior,after),'Unexpected kernel source revision'
work=Path('/root/t110-build/gateway-route-backport');work.mkdir(exist_ok=True)
for name,data in [('base.c',before),('candidate.c',after)]:
 target=work/name
 if target.exists():
  assert target.read_text() in (data,prior) if name=='candidate.c' else target.read_text()==data
  target.write_text(data)
 else:target.write_text(data)
patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/net/ipv4/fib_semantics.c',tofile='b/net/ipv4/fib_semantics.c'))
(p/'patches/0097-kernel-explicit-table-gateway-validation.patch').write_text(patch)
src.write_text(after)
(e/'gateway-source.json').write_text(json.dumps(dict(path='net/ipv4/fib_semantics.c',before_sha256=hashlib.sha256(before.encode()).hexdigest(),after_sha256=hashlib.sha256(after.encode()).hexdigest(),reference='uid-upstream/gateway-mainline-reference.json',user_packet_routing_unchanged=True),indent=2)+'\n')
print('GATEWAY_SOURCE_READY',hashlib.sha256(after.encode()).hexdigest())
