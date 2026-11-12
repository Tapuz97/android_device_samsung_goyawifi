// SPDX-License-Identifier: Apache-2.0
// Bounded H4 Reset/Read Local Version transport check; no pairing or BD_ADDR write.
#include <array>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <poll.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#include <vector>

static long long nowMs() {
    timespec ts{}; clock_gettime(CLOCK_MONOTONIC, &ts);
    return static_cast<long long>(ts.tv_sec)*1000 + ts.tv_nsec/1000000;
}
// Return complete packet length, 0 for a fragment, -1 for an invalid H4 type.
static int packetLength(const std::vector<unsigned char>& b) {
    if (b.empty()) return 0;
    if (b[0] == 4) return b.size()<3 ? 0 : 3+b[2];
    if (b[0] == 2) return b.size()<5 ? 0 : 5+b[3]+256*b[4];
    if (b[0] == 3) return b.size()<4 ? 0 : 4+b[3];
    return -1;
}
static int selfTest() {
    int checks=0;
    auto check=[&](bool ok){++checks;if(!ok){fprintf(stderr,"SELF_TEST_FAILED %d\n",checks);return false;}return true;};
    if (!check(packetLength({})==0) || !check(packetLength({4,14})==0) ||
        !check(packetLength({4,14,4})==7) || !check(packetLength({2,1,0,2,0})==7) ||
        !check(packetLength({3,1,0,2})==6) || !check(packetLength({0xff})==-1)) return 1;
    std::vector<unsigned char> fragment{4,14,4,1,3,12};
    if (!check(fragment.size()<static_cast<size_t>(packetLength(fragment)))) return 1;
    fragment.push_back(0);
    if (!check(fragment.size()==static_cast<size_t>(packetLength(fragment)) && fragment[4]==3 && fragment[5]==12 && fragment[6]==0)) return 1;
    printf("H4_SELF_TEST_PASS %d\n",checks); return 0;
}
static int loadModule() {
    if(getuid()!=0 || getpid()==1)return 2;
    int fd=open("/data/local/tmp/t110-bt-module-0100.ko",O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
    if(fd<0){perror("open Bluetooth module");return 1;}
    struct stat st{};
    if(fstat(fd,&st) || !S_ISREG(st.st_mode) || st.st_uid!=0 ||
            (st.st_mode&0077) || st.st_size<64 || st.st_size>2*1024*1024){close(fd);return 2;}
    size_t size=st.st_size;void* data=mmap(nullptr,size,PROT_READ,MAP_PRIVATE,fd,0);close(fd);
    if(data==MAP_FAILED){perror("map Bluetooth module");return 1;}
    const auto* bytes=static_cast<const unsigned char*>(data);
    if(memcmp(bytes,"\177ELF\1\1",6) || bytes[18]!=40 || bytes[19]!=0){munmap(data,size);return 2;}
    long result=syscall(SYS_init_module,data,size,
        "fw=1 drv_mode=1 debug_intf=0 require_fw_ready=1 req_fw_nowait=0");
    if(result)perror("init_module Bluetooth");
    munmap(data,size);return result?1:0;
}
static bool command(int fd, unsigned opcode, std::vector<unsigned char>& pending) {
    const unsigned char bytes[]{1, static_cast<unsigned char>(opcode),static_cast<unsigned char>(opcode>>8),0};
    if(write(fd,bytes,sizeof(bytes))!=sizeof(bytes)){perror("H4 write");return false;}
    const auto deadline=nowMs()+4000;
    while(nowMs()<deadline) {
        while(!pending.empty()) {
            int length=packetLength(pending);
            if(length<0 || length>4096){fprintf(stderr,"Invalid H4 framing\n");return false;}
            if(!length || pending.size()<static_cast<size_t>(length))break;
            if(pending[0]==4 && pending[1]==14 && length>=7 &&
                    (static_cast<unsigned>(pending[4]) | static_cast<unsigned>(pending[5])<<8)==opcode) {
                unsigned status=pending[6];
                printf("COMMAND_COMPLETE opcode=0x%04x status=%u bytes=%d",opcode,status,length);
                if(opcode==0x1001 && length>=15)
                    printf(" hci_version=%u hci_revision=%u lmp_version=%u manufacturer=%u subversion=%u",
                        pending[7],pending[8]+256*pending[9],pending[10],pending[11]+256*pending[12],pending[13]+256*pending[14]);
                if(opcode==0x1003 && length>=15) {
                    printf(" features=");for(int i=7;i<15;++i)printf("%02x",pending[i]);
                }
                if(opcode==0x1009) {
                    bool any=false,allFF=true;
                    if(length!=13)return false;
                    for(int i=7;i<13;++i){any|=pending[i]!=0;allFF&=pending[i]==255;}
                    printf(" controller_address_valid=%u",any&&!allFF);
                    if(!any||allFF)return false;
                }
                printf("\n");pending.erase(pending.begin(),pending.begin()+length);return status==0;
            }
            if(pending[0]==4 && pending[1]==15 && length>=7 &&
                    (static_cast<unsigned>(pending[5]) | static_cast<unsigned>(pending[6])<<8)==opcode && pending[3]!=0) {
                fprintf(stderr,"COMMAND_STATUS_ERROR opcode=%04x status=%u\n",opcode,pending[3]);return false;
            }
            pending.erase(pending.begin(),pending.begin()+length);
        }
        const auto remaining=deadline-nowMs();if(remaining<=0)break;
        pollfd poller{fd,POLLIN,0};int ready=poll(&poller,1,static_cast<int>(remaining));
        if(ready<0){if(errno==EINTR)continue;perror("H4 poll");return false;}
        if(!ready)continue;
        if(poller.revents&(POLLERR|POLLHUP|POLLNVAL)){fprintf(stderr,"H4 poll disconnected\n");return false;}
        std::array<unsigned char,1024> buffer{};ssize_t n=read(fd,buffer.data(),buffer.size());
        if(n<0 && (errno==EAGAIN||errno==EINTR))continue;
        if(n<=0){perror("H4 read");return false;}
        pending.insert(pending.end(),buffer.begin(),buffer.begin()+n);
        if(pending.size()>8192){fprintf(stderr,"H4 pending limit exceeded\n");return false;}
    }
    fprintf(stderr,"H4_COMMAND_TIMEOUT opcode=0x%04x\n",opcode);return false;
}
int main(int argc,char** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);
    if(argc==2 && !strcmp(argv[1],"--self-test"))return selfTest();
    if(argc==2 && !strcmp(argv[1],"--load-module"))return loadModule();
    if(argc!=1 || getuid()!=0 || getpid()==1){fprintf(stderr,"Use root diagnostic ADB with no arguments\n");return 2;}
    alarm(15);struct stat st{};
    if(lstat("/dev/mbtchar0",&st) || !S_ISCHR(st.st_mode) || (st.st_mode&0007)) {
        fprintf(stderr,"Expected restricted real Bluetooth character node\n");return 2;
    }
    int fd=open("/dev/mbtchar0",O_RDWR|O_NONBLOCK|O_CLOEXEC);
    if(fd<0){perror("open Bluetooth character node");return 1;}
    std::vector<unsigned char> pending;
    bool ok=command(fd,0x0c03,pending) && command(fd,0x1001,pending) && command(fd,0x1003,pending) && command(fd,0x1009,pending);
    close(fd);puts(ok?"BLUETOOTH_H4_TRANSPORT_PASS":"BLUETOOTH_H4_TRANSPORT_FAIL");return ok?0:1;
}
