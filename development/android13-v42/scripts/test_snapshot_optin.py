"""Exercise actual bootstrap logging in isolated roots; never run a real worker."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
assert os.environ.get('WSL_DISTRO_NAME')=='Ubuntu'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');e=p/'evidence/ui-system-hang-20261112'
s=(p/'work/core-boot/stage.c').read_text();start=s.index('static void label_log_fd(');end=s.index('\n#endif\n#endif\n\nstatic void mount_fs',start);actual=s[start:end]
headers='''#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
static int checkpoint_fd=-1, forks;
static void fail(const char *text) { perror(text);exit(7); }
static void checkpoint(const char *text) { if(checkpoint_fd>=0)dprintf(checkpoint_fd,"%s\\n",text); }
static int test_label(int fd,const char *name,const void *value,size_t size,int flags) {
 (void)fd;(void)flags;if(strcmp(name,"security.selinux") || size!=sizeof("u:object_r:t110_bootlog_file:s0") || strcmp(value,"u:object_r:t110_bootlog_file:s0"))abort();return 0;
}
static int test_klog(int type,char *buffer,int length) {
 const char *message="one early kernel snapshot\\n";
 if(type!=3 || length<(int)strlen(message))abort();
 memcpy(buffer,message,strlen(message));return (int)strlen(message);
}
static pid_t test_fork(void) { forks++;return 12345; }
static void test_sync(void) {}
#define fsetxattr test_label
#define klogctl test_klog
#define fork test_fork
#define sync test_sync
'''
main='''
int main(int argc,char **argv) {
 if(argc!=3 || chroot(argv[1]) || chdir("/"))fail("isolated test root");
 persistent_logging();
 int expected=atoi(argv[2]);if(forks!=expected)return 9;
 struct stat info;
 if(stat("/stage-data/local/tmp/t110-bootlogs/boot-0001/kernel-0.txt",&info))return 10;
 if(expected==0 && info.st_size!=sizeof("one early kernel snapshot\\n")-1)return 11;
 if(access("/stage-data/local/tmp/t110-bootlogs/boot-0001/checkpoints.txt",R_OK))return 12;
 printf("snapshot opt-in case passed: forks=%d\\n",forks);return 0;
}
'''
results=[]
with tempfile.TemporaryDirectory(prefix='t110-snapshot-test-') as tmp:
 t=Path(tmp);source=t/'fixture.c';source.write_text(headers+actual+main)
 subprocess.run(['gcc','-static','-O2','-Wall','-Wextra','-Werror',str(source),'-o',str(t/'fixture')],check=True)
 for name,kind,expected in [('default','absent',0),('explicit','file',1),('symlink','symlink',0),('writable','writable',0),('directory','directory',0)]:
  root=t/name;parent=root/'stage-data/local/tmp/t110-bootlogs';parent.mkdir(parents=True);marker=parent/'periodic-enabled'
  if kind in ['file','writable']:marker.write_text('');marker.chmod(0o600 if kind=='file' else 0o666)
  elif kind=='symlink':marker.symlink_to('/not-a-trusted-marker')
  elif kind=='directory':marker.mkdir()
  r=subprocess.run([str(t/'fixture'),str(root),str(expected)],capture_output=True,text=True)
  assert r.returncode==0,(name,r.returncode,r.stdout,r.stderr)
  results.append(dict(case=name,expected_worker_forks=expected,result=r.stdout.strip()))
record=dict(status='PASS',actual_function_sha256=hashlib.sha256(actual.encode()).hexdigest(),cases=results,real_fork_or_syslog_access=False,tablet_access=False)
(e/'snapshot-optin-regressions.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
