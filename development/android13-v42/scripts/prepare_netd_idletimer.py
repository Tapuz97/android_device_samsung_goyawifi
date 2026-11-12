"""Accept the legacy kernel's LABEL attribute and reject missing timer labels."""
from pathlib import Path
import difflib,hashlib,json,subprocess,sys
p=Path(__file__).resolve().parents[1];tree=Path(sys.argv[1]);repo=tree/'system/netd';name='server/NetlinkHandler.cpp';f=repo/name
patch=p/'patches/0099-netd-accept-legacy-idletimer-label.patch'
if not patch.exists():
 before=f.read_text();after=before
 start=after.index('    } else if (!strcmp(subsys, "xt_idletimer")) {')
 end=after.index('\n#if !LOG_NDEBUG',start)
 replacement='''    } else if (!strcmp(subsys, "xt_idletimer")) {
        if (const auto activity = parseIdletimerActivity(*evt)) {
            notifyInterfaceClassActivityChanged(activity->label, activity->active,
                                                activity->timestamp, activity->uid);
        }
'''
 after=after[:start]+replacement+after[end:]
 include='#include "NetlinkHandler.h"'
 assert after.count(include)==1;after=after.replace(include,include+'\n#include "IdletimerEvent.h"',1)
 changes={name:(before,after)}
 for filename in ['IdletimerEvent.h','IdletimerEventTest.cpp']:
  assert not(repo/'server'/filename).exists()
  changes['server/'+filename]=('',(p/'scripts/netd-idletimer'/filename).read_text())
 bp=repo/'server/Android.bp';before_bp=bp.read_text()
 after_bp=before_bp+'''
cc_test {
    name: "netd_idletimer_event_test",
    srcs: ["IdletimerEventTest.cpp"],
    shared_libs: ["libbase", "liblog", "libsysutils"],
    test_suites: ["device-tests"],
}
'''
 changes['server/Android.bp']=(before_bp,after_bp)
 chunks=[]
 for filename,(old,new) in changes.items():
  chunks.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),'/dev/null' if not old else 'a/'+filename,'b/'+filename))
 patch.write_text(''.join(chunks),encoding='utf-8')
cmd=['git','-C',str(repo),'apply']
if subprocess.run(cmd+['--reverse','--check',str(patch)],capture_output=True).returncode:
 subprocess.run(cmd+['--check',str(patch)],check=True);subprocess.run(cmd+[str(patch)],check=True)
e=p/'evidence/hardware-v35/netd-event'
(e/'source.json').write_text(json.dumps(dict(status='SOURCE_APPLIED',files={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in ['server/NetlinkHandler.cpp','server/IdletimerEvent.h','server/IdletimerEventTest.cpp','server/Android.bp']},patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),kernel_format='LABEL=n, STATE=active|inactive',crash='ParseInt(nullptr) from NetlinkHandler::onEvent'),indent=2)+'\n',encoding='utf-8')
print('NETD_LEGACY_LABEL_SOURCE_READY')
