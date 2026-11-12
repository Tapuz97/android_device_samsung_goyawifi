"""Compile the actual init FD-dump and fatal-target parsing code in a host harness."""
from pathlib import Path
import subprocess
import tempfile

root = Path('/root/t110-build/lineage20/system/core/init')
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
source = (root / 'init.cpp').read_text()
dump = source[source.index('static void DumpPidFds('):source.index('static void DumpFile(')]
source = (root / 'reboot_utils.cpp').read_text()
start = source.index('    const std::string kRebootTargetString = ')
end = source.index('\nbool IsRebootCapable()', start)
parse = source[start:end].rstrip()
assert parse.endswith('}')
parse = parse[:-1]
prelude = r'''
#include <filesystem>
#include <iostream>
#include <string>
#include <unistd.h>
#define LOG(level) std::cerr
namespace android::base {
bool Readlink(const std::filesystem::path& path, std::string* out) {
    char buf[4096];
    auto n = readlink(path.c_str(), buf, sizeof(buf));
    if (n < 0) return false;
    out->assign(buf, n);
    return true;
}
}
template<class F> void ImportBootconfig(F) {}
static std::string init_fatal_reboot_target;
'''
main = r'''
int main() {
    ParseTarget("console=ttyAMA0 androidboot.init_fatal_reboot_target=recovery extra=1");
    if (init_fatal_reboot_target != "recovery") return 1;
    ParseTarget("androidboot.init_fatal_reboot_target=recovery");
    if (init_fatal_reboot_target != "recovery") return 2;
    ParseTarget("androidboot.init_fatal_reboot_target=bootloader");
    if (init_fatal_reboot_target != "bootloader") return 3;
    // Reproduce the unprivileged /proc/<other pid>/fd case that crashed init.
    if (setgid(65534) || setuid(65534)) return 4;
    std::error_code ec;
    std::filesystem::directory_iterator denied("/proc/1/fd", ec);
    if (!ec) return 5;
    try {
        DumpPidFds("FDTEST missing: ", -1);
        DumpPidFds("FDTEST denied: ", 1);
        DumpPidFds("FDTEST own: ", getpid());
    } catch (const std::filesystem::filesystem_error& e) {
        std::cerr << "UNEXPECTED_EXCEPTION " << e.what() << '\n';
        return 6;
    }
    std::cout << "\nINIT_DIAGNOSTICS_AND_FATAL_TARGET_PASS\n";
}
'''
with tempfile.TemporaryDirectory(prefix='t110-init-test-') as temp:
    p = Path(temp)
    code = prelude + dump + '\nstatic void ParseTarget(const std::string& cmdline) {\n' + parse + '\n}\n' + main
    (p / 'test.cpp').write_text(code)
    subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror', str(p / 'test.cpp'), '-o', str(p / 'test')], check=True)
    result = subprocess.run([str(p / 'test')], capture_output=True, text=True, timeout=10)
    log = result.stdout + result.stderr
    (project / 'evidence/init-diagnostics-regression.log').write_text(log)
    print(log)
    assert result.returncode == 0, result.returncode
    assert 'Cannot inspect /proc/-1/fd' in log and 'Cannot inspect /proc/1/fd' in log
