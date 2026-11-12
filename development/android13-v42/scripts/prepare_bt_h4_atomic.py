"""Preserve a Marvell H4 packet in one character-device write; retain UART mode."""
from pathlib import Path
import difflib,hashlib,json,os
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');root=Path('/root/t110-build/lineage20/hardware/interfaces');e=p/'evidence/hardware-bt-sd'
prefix='bluetooth/1.0/default/';patch=p/'patches/0101-bluetooth-packetized-h4-transport.patch';record=e/'h4-production-source.json'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
if record.exists():
 for name,expected in json.loads(record.read_text())['files'].items():assert sha(root/name)==expected,name
 print('PACKET_H4_ALREADY_APPLIED');raise SystemExit(0)
assert not patch.exists();changes={}
def change(name,transform):
 f=root/(prefix+name);before=f.read_text();after=transform(before);assert after!=before,name;changes[prefix+name]=(before,after)
def header(s):
 old='PacketReadCallback sco_cb, PacketReadCallback iso_cb)';assert s.count(old)==1
 s=s.replace(old,'PacketReadCallback sco_cb, PacketReadCallback iso_cb,\n             bool packetized_writes = false)')
 s=s.replace('hci_packetizer_([this]() { OnPacketReady(); }) {}','hci_packetizer_([this]() { OnPacketReady(); }),\n        packetized_writes_(packetized_writes) {}')
 s=s.replace('  int uart_fd_;','  int uart_fd_;').replace('  hci::HciPacketizer hci_packetizer_;','  hci::HciPacketizer hci_packetizer_;\n  const bool packetized_writes_;')
 return s
def send(s):
 marker='size_t H4Protocol::Send(uint8_t type, const uint8_t* data, size_t length) {';assert s.count(marker)==1
 return s.replace(marker,marker+'''
  if (packetized_writes_) {
    // mbtchar consumes one complete H4 packet per write. Its legacy VFS
    // writev fallback calls ->write separately for each iovec, so an H4 type
    // iovec followed by a payload iovec would become two corrupt packets.
    if (data == nullptr || length == 0 || length > 65539) return 0;
    std::vector<uint8_t> packet(length + 1);
    packet[0] = type;
    memcpy(packet.data() + 1, data, length);
    ssize_t result = TEMP_FAILURE_RETRY(write(uart_fd_, packet.data(), packet.size()));
    if (result != static_cast<ssize_t>(packet.size())) {
      // A short packet must never be retried as a fresh H4 packet tail.
      ALOGE("%s incomplete packet write (%zd/%zu)", __func__, result, packet.size());
      return 0;
    }
    return result;
  }
''')
def vendor(s):
 s=s.replace('#include <fcntl.h>','#include <fcntl.h>\n#include <sys/stat.h>')
 old='new hci::H4Protocol(fd_list[0], intercept_events, acl_cb, sco_cb, iso_cb);';assert s.count(old)==1
 new='''new hci::H4Protocol(fd_list[0], intercept_events, acl_cb, sco_cb, iso_cb,
            [&]() {
              struct stat node{}, descriptor{};
              return lstat("/dev/mbtchar0", &node) == 0 && S_ISCHR(node.st_mode) &&
                     fstat(fd_list[0], &descriptor) == 0 && S_ISCHR(descriptor.st_mode) &&
                     descriptor.st_rdev == node.st_rdev;
            }());'''
 return s.replace(old,new)
def tests(s):
 s=s.replace('#include <sys/socket.h>','#include <sys/socket.h>\n#include <sys/eventfd.h>')
 s+='''
namespace android::hardware::bluetooth::hci {
// eventfd requires each kernel write call to contain exactly eight bytes.
// A split type/payload write fails; this checks the production Send method's
// syscall boundary rather than merely comparing concatenated stream bytes.
TEST(T110AtomicH4Test, CompletePacketUsesOneKernelWrite) {
  int fd = eventfd(0, EFD_NONBLOCK | EFD_CLOEXEC);
  ASSERT_GE(fd, 0);
  auto ignore = [](const hidl_vec<uint8_t>&) {};
  H4Protocol protocol(fd, ignore, ignore, ignore, ignore, true);
  uint8_t payload[7] = {};
  EXPECT_EQ(size_t{8}, protocol.Send(1, payload, sizeof(payload)));
  uint64_t counter = 0;
  EXPECT_EQ(ssize_t{8}, read(fd, &counter, sizeof(counter)));
  EXPECT_EQ(uint64_t{1}, counter);
  close(fd);
}
TEST(T110AtomicH4Test, InvalidPacketDoesNotWriteOrReadPastInput) {
  int fd = eventfd(0, EFD_NONBLOCK | EFD_CLOEXEC);
  ASSERT_GE(fd, 0);
  auto ignore = [](const hidl_vec<uint8_t>&) {};
  H4Protocol protocol(fd, ignore, ignore, ignore, ignore, true);
  uint8_t payload = 0;
  EXPECT_EQ(size_t{0}, protocol.Send(1, nullptr, 7));
  EXPECT_EQ(size_t{0}, protocol.Send(1, &payload, 0));
  EXPECT_EQ(size_t{0}, protocol.Send(1, &payload, 65540));
  uint64_t counter = 0;
  EXPECT_EQ(ssize_t{-1}, read(fd, &counter, sizeof(counter)));
  EXPECT_EQ(EAGAIN, errno);
  close(fd);
}
}  // namespace android::hardware::bluetooth::hci
'''
 return s
change('h4_protocol.h',header);change('h4_protocol.cc',send);change('vendor_interface.cc',vendor);change('test/h4_protocol_unittest.cc',tests)
chunks=[]
for name,(before,after) in changes.items():chunks.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),'a/'+name,'b/'+name))
patch.write_text(''.join(chunks))
for name,(_,after) in changes.items():(root/name).write_text(after)
record.write_text(json.dumps(dict(files={name:sha(root/name) for name in changes},patch_sha256=sha(patch),status='SOURCE_APPLIED_NOT_BUILT'),indent=2)+'\n');print('PACKET_H4_SOURCE_READY')
