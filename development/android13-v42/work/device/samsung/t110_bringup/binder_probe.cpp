#include <binder/Binder.h>
#include <binder/IBinder.h>
#include <binder/IPCThreadState.h>
#include <binder/Parcel.h>
#include <binder/ProcessState.h>
#include <signal.h>
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>
using namespace android;
class Echo final : public BBinder {
 status_t onTransact(uint32_t code,const Parcel& data,Parcel* reply,uint32_t flags) override {
  if(code!=FIRST_CALL_TRANSACTION)return BBinder::onTransact(code,data,reply,flags);
  int32_t value=0;status_t status=data.readInt32(&value);if(status!=OK)return status;
  return reply->writeInt32(value ^ 0x13579bdf);
 }
};
int main() {
 if(getuid()!=0 || access("/sbin/recovery",X_OK) || access("/dev/vndbinder",R_OK|W_OK)){fprintf(stderr,"Run only in the root diagnostic environment\n");return 2;}
 // Use only vndbinder, which is unused by the diagnostic recovery userspace.
 // Never run this while a vendor service manager owns that device.
 int ready[2];if(pipe(ready))return 2;
 alarm(20);pid_t server=fork();if(server<0)return 2;
 if(!server){
  close(ready[0]);alarm(20);
  auto process=ProcessState::initWithDriver("/dev/vndbinder");
  IPCThreadState::self()->setTheContextObject(sp<Echo>::make());
  char ok=process->becomeContextManager()?'Y':'N';
  if(write(ready[1],&ok,1)!=1||ok!='Y')_exit(3);close(ready[1]);
  IPCThreadState::self()->joinThreadPool();_exit(4);
 }
 close(ready[1]);char ok=0;int result=1;
 if(read(ready[0],&ok,1)==1 && ok=='Y'){
  auto process=ProcessState::initWithDriver("/dev/vndbinder");
  auto remote=process->getContextObject(nullptr);
  Parcel request,reply;int32_t answer=0;
  if(remote && request.writeInt32(0x2468)==OK &&
     remote->transact(IBinder::FIRST_CALL_TRANSACTION,request,&reply)==OK &&
     reply.readInt32(&answer)==OK && answer==(0x2468 ^ 0x13579bdf))result=0;
 }
 close(ready[0]);kill(server,SIGKILL);waitpid(server,nullptr,0);alarm(0);
 printf("%s Android 13 libbinder cross-process Parcel roundtrip\n",result?"FAIL":"PASS");return result;
}
