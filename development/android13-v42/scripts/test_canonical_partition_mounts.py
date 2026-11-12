"""Exercise the actual bootstrap block, including wrong-target rejection and real binds."""
from pathlib import Path
import json,os,subprocess,tempfile
assert os.environ.get('WSL_DISTRO_NAME')=='Ubuntu'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/ui-system-hang-20261112'
s=(p/'work/core-boot/stage.c').read_text();begin=s.index('#ifdef T110_FULL_BOOT\n    /* ART stores class-loader paths');end=s.index('#endif\n    checkpoint("Android system mounted");',begin)+len('#endif\n');block=s[begin:end]
headers='#define _GNU_SOURCE\n#define T110_FULL_BOOT\n#include <sys/stat.h>\n#include <sys/mount.h>\n#include <sys/statvfs.h>\n#include <errno.h>\n#include <unistd.h>\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <setjmp.h>\n'
mock=headers+'''
static jmp_buf failed;
static int calls,kind,checkpoints;
static void fail(const char *message) { (void)message; longjmp(failed,1); }
static int test_lstat(const char *path,struct stat *value) {
 (void)path; memset(value,0,sizeof(*value));
 if(kind==3) { errno=ENOENT;return -1; }
 value->st_mode=kind==1 ? S_IFLNK|0777 : kind==2 ? S_IFREG|0644 : S_IFDIR|0755;
 return 0;
}
static void mount_fs(const char *source,const char *target,const char *type,unsigned long flags,const char *data) {
 const char *sources[]={"/system/product","/system/system_ext"};
 const char *targets[]={"/product","/system_ext"};
 if(calls>=2 || strcmp(source,sources[calls]) || strcmp(target,targets[calls]) || type || flags!=MS_BIND || data) abort();
 calls++;
}
static void checkpoint(const char *message) { if(!strstr(message,"canonical partition roots")) abort();checkpoints++; }
#define lstat test_lstat
static void run(void) {
'''+block+'''
}
int main(void) {
 if(setjmp(failed)) return 1;
 run();if(calls!=2 || checkpoints!=1)return 2;
 for(kind=1;kind<=3;kind++) {
  calls=0;checkpoints=0;
  if(!setjmp(failed)) {run();return 3;}
  if(calls || checkpoints)return 4;
 }
 puts("actual bootstrap block: two correct binds; symlink, regular and missing targets rejected");return 0;
}
'''
real=headers+'''
static void fail(const char *message) { perror(message);exit(1); }
static void mount_fs(const char *source,const char *target,const char *type,unsigned long flags,const char *data) { if(mount(source,target,type,flags,data))fail(target); }
static void checkpoint(const char *message) { puts(message); }
int main(int argc,char **argv) {
 if(argc!=2 || chroot(argv[1]) || chdir("/"))fail("isolated test root");
'''+block+'''
 const char *aliases[]={"/product/probe","/system_ext/probe"};
 const char *sources[]={"/system/product/probe","/system/system_ext/probe"};
 for(int i=0;i<2;i++) {
  char resolved[4096];struct stat a,b;struct statvfs fs;
  if(!realpath(aliases[i],resolved) || strcmp(resolved,aliases[i]))fail("canonical root");
  if(stat(aliases[i],&a) || stat(sources[i],&b) || a.st_ino!=b.st_ino || a.st_dev!=b.st_dev)fail("same actual file");
  if(statvfs(aliases[i],&fs) || !(fs.f_flag&ST_RDONLY))fail("read-only bind");
 }
 puts("real read-only binds preserve canonical names and exact underlying files");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='t110-canonical-roots-') as temporary:
    t=Path(temporary)
    for name,code in [('mock',mock),('real',real)]:
        (t/(name+'.c')).write_text(code)
        subprocess.run(['gcc','-static','-O2','-Wall','-Wextra','-Werror',str(t/(name+'.c')),'-o',str(t/name)],check=True)
    mocked=subprocess.run([str(t/'mock')],capture_output=True,text=True,check=True)
    # Mounts exist only in this child namespace; its exit releases every mount.
    setup='''import os,subprocess,sys
from pathlib import Path
base=Path(sys.argv[1]);root=base/'root';(root/'system').mkdir(parents=True)
subprocess.run(['mount','-t','tmpfs','tmpfs',str(root/'system')],check=True)
for name in ['product','system_ext']:
 (root/'system'/name).mkdir();(root/'system'/name/'probe').write_text('unchanged library file')
 (root/name).mkdir()
subprocess.run(['mount','-o','remount,ro',str(root/'system')],check=True)
subprocess.run([str(base/'real'),str(root)],check=True)
'''
    native=subprocess.run(['unshare','--mount','--fork','python3','-c',setup,str(t)],capture_output=True,text=True)
    record=dict(actual_bootstrap_block_mock_exit=mocked.returncode,mock_output=mocked.stdout,real_namespace_exit=native.returncode,
                real_namespace_output=native.stdout,real_namespace_error=native.stderr,tablet_access=False)
    assert native.returncode==0,record
    record['status']='PASS';(e/'canonical-root-regressions.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
