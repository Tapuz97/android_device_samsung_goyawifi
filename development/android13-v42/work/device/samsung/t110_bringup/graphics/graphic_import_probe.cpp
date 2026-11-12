// SPDX-License-Identifier: Apache-2.0
// Intentionally no EGL/GLES dependency. Match an import-only Binder consumer.
#include "GpuReadbackProtocol.h"
#include <thread>
#include <binder/IServiceManager.h>
#include <binder/Parcel.h>
#include <gui/ScreenCaptureResults.h>
using namespace android;
int main(int argc,char** argv) {
    if(argc!=4)return 2;
    if(!strcmp(argv[1],"--binder")) {
        auto service=defaultServiceManager()->checkService(String16(argv[2]));
        if(!service){printf("%s service_missing\n",argv[3]);return 25;}
        Parcel request,reply;status_t status=service->transact(IBinder::FIRST_CALL_TRANSACTION,request,&reply);
        if(status!=NO_ERROR){printf("%s transact=%d\n",argv[3],status);return 26;}
        gui::ScreenCaptureResults results;status=results.readFromParcel(&reply);
        if(status!=NO_ERROR){printf("%s parcel_read=%d\n",argv[3],status);return 27;}
        reply.freeData();
        if(!results.buffer)return 28;
        return checkPixels(results.buffer,argv[3])?0:29;
    }
    int result=99;
    if(!strcmp(argv[1],"--receive-main")) {
        printf("%s receiver=main pid=%d tid=%d\n",argv[3],getpid(),gettid());
        return receiveBuffer(atoi(argv[2]),argv[3]);
    }
    std::thread worker([&]{
        printf("%s receiver=worker pid=%d tid=%d\n",argv[3],getpid(),gettid());
        result=receiveBuffer(atoi(argv[2]),argv[3]);
    });
    worker.join();return result;
}
