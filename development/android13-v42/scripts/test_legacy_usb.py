"""Exercise actual T110 transport header framing and cancellation with sockets."""
import subprocess
from pathlib import Path
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
work = Path('/root/t110-build/legacy-usb-test')
work.mkdir(exist_ok=True)
prefix = r'''
#include <algorithm>
#include <cassert>
#include <cerrno>
#include <chrono>
#include <fcntl.h>
#include <future>
#include <iostream>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
#include <sys/socket.h>
#include <unistd.h>
#define CHECK(x) assert(x)
#define CHECK_EQ(x,y) assert((x)==(y))
#define LOG(x) std::cerr
#define PLOG(x) std::cerr
constexpr size_t MAX_PAYLOAD=1024*1024;
struct RSA {};
struct unique_fd {
 int fd; unique_fd(int f=-1):fd(f){} ~unique_fd(){reset();}
 unique_fd(unique_fd&& o):fd(o.fd){o.fd=-1;}
 unique_fd(const unique_fd&)=delete;
 int get()const{return fd;} void reset(){if(fd>=0)close(fd);fd=-1;}
};
struct amessage {uint32_t command,arg0,arg1,data_length,data_check,magic;};
struct apacket {amessage msg{};std::vector<char> payload;};
struct BlockingConnection {
 virtual ~BlockingConnection()=default;
 virtual bool Read(apacket*)=0;virtual bool Write(apacket*)=0;
 virtual bool DoTlsHandshake(RSA*,std::string*)=0;
 virtual void Close()=0;virtual void Reset()=0;
};
'''
suffix = r'''
static void exact(int fd, void* buffer, size_t length, bool writing) {
 auto p=static_cast<char*>(buffer);
 while(length) {ssize_t n=writing?write(fd,p,length):read(fd,p,length); assert(n>0);p+=n;length-=n;}
}
int main() {
 alarm(20);
 for(int trial=0;trial<12;++trial) {
  int fds[2];assert(!socketpair(AF_UNIX,SOCK_STREAM,0,fds));unique_fd host(fds[0]);
  std::promise<void> notifier;auto done=notifier.get_future();
  {
   T110LegacyUsbConnection connection(unique_fd(open("/dev/null",O_RDWR)),unique_fd(dup(fds[1])),unique_fd(fds[1]),std::move(notifier));
   apacket out;out.msg.command=0x12345678;out.msg.magic=out.msg.command^0xffffffffU;
   out.payload.assign(128*1024,'x');out.msg.data_length=out.payload.size();
   apacket in;
   std::thread reader([&]{assert(connection.Read(&in));});
   exact(host.get(),&out.msg,sizeof(out.msg),true);exact(host.get(),out.payload.data(),out.payload.size(),true);reader.join();assert(in.payload==out.payload);
   std::thread writer([&]{assert(connection.Write(&out));});
   amessage header;exact(host.get(),&header,sizeof(header),false);
   std::vector<char> payload(header.data_length);exact(host.get(),payload.data(),payload.size(),false);writer.join();assert(payload==out.payload);
   bool result=true;
   if(trial%2==0) {
    std::thread blocked([&]{apacket packet;result=connection.Read(&packet);});
    std::this_thread::sleep_for(std::chrono::milliseconds(20));connection.Close();blocked.join();
   } else {
    out.payload.assign(MAX_PAYLOAD,'z');out.msg.data_length=out.payload.size();
    std::thread blocked([&]{result=connection.Write(&out);});
    std::this_thread::sleep_for(std::chrono::milliseconds(20));connection.Close();blocked.join();
   }
   assert(!result);
   connection.Close();
  }
  assert(done.wait_for(std::chrono::milliseconds(100))==std::future_status::ready);
 }
 std::cout<<"PASS 12 transport cycles: 128KiB bidirectional framing, blocked read/write cancellation, repeated close, destruction notification\n";
}
'''
(work / 'test.cpp').write_text(prefix + (project / 'work/native-ramdisk/usb_legacy_t110.h').read_text() + suffix)
subprocess.run(['g++','-std=c++17','-g','-O1','-pthread','-fsanitize=address,undefined',str(work/'test.cpp'),'-o',str(work/'test')],check=True)
result=subprocess.run([str(work/'test')],capture_output=True,text=True,timeout=25)
dest=project/'artifacts/legacy-usb-regression'
dest.mkdir(exist_ok=True)
(dest/'test.cpp').write_text((work/'test.cpp').read_text())
(dest/'test.log').write_text(result.stdout+result.stderr)
assert result.returncode==0,result.stderr
print(result.stdout)
