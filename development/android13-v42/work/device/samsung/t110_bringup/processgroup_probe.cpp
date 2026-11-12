#include <android-base/file.h>
#include <android-base/properties.h>
#include <processgroup/processgroup.h>
#include <linux/magic.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <sys/statfs.h>
#include <sys/wait.h>
#include <unistd.h>
#include <string>

int main() {
    if (getuid() != 0 || access("/t110-native-diagnostic", F_OK) ||
        !android::base::GetBoolProperty("ro.t110.legacy_processgroups", false)) {
        fprintf(stderr, "Requires the dedicated modern T110 diagnostic ramdisk\n");
        return 2;
    }
    std::string root;
    struct statfs fs;
    if (!CgroupGetControllerPath("cpuacct", &root) || statfs(root.c_str(), &fs) ||
        fs.f_type != CGROUP_SUPER_MAGIC) {
        fprintf(stderr, "cpuacct is not a mounted v1 cgroup filesystem\n");
        return 3;
    }
    constexpr uid_t test_uid = 29000;
    int commands[2], reports[2];
    if (pipe(commands) || pipe(reports)) return 4;
    alarm(30);
    pid_t child = fork();
    if (child < 0) return 5;
    if (!child) {
        alarm(25);
        close(commands[1]);
        close(reports[0]);
        if (setpgid(0, 0)) _exit(6);
        char ready = 'R';
        if (!android::base::WriteFully(reports[1], &ready, 1) ||
            !android::base::ReadFully(commands[0], &ready, 1)) _exit(7);
        pid_t descendant = fork();
        if (descendant < 0) _exit(8);
        if (!descendant) {
            alarm(20);
            close(commands[0]);
            close(reports[1]);
            for (;;) pause();
        }
        if (!android::base::WriteFully(reports[1], &descendant, sizeof(descendant))) _exit(9);
        for (;;) pause();
    }
    close(commands[0]);
    close(reports[1]);
    int result = 1;
    bool created = false;
    char ready;
    std::string group = root + "/uid_" + std::to_string(test_uid) + "/pid_" + std::to_string(child);
    if (android::base::ReadFully(reports[0], &ready, 1) && ready == 'R' &&
        access(group.c_str(), F_OK) == -1 && errno == ENOENT &&
        createProcessGroup(test_uid, child, false) == 0) {
        created = true;
        pid_t descendant;
        std::string members;
        if (android::base::WriteFully(commands[1], &ready, 1) &&
            android::base::ReadFully(reports[0], &descendant, sizeof(descendant)) &&
            android::base::ReadFileToString(group + "/cgroup.procs", &members)) {
            members = "\n" + members;
            bool inherited = members.find("\n" + std::to_string(child) + "\n") != std::string::npos &&
                             members.find("\n" + std::to_string(descendant) + "\n") != std::string::npos;
            if (inherited && killProcessGroup(test_uid, child, SIGKILL) == 0 &&
                access(group.c_str(), F_OK) == -1 && errno == ENOENT) result = 0;
        }
    }
    // Only the freshly forked child and its private process group are affected.
    kill(-child, SIGKILL);
    kill(child, SIGKILL);
    if (created) killProcessGroup(test_uid, child, SIGKILL);
    TEMP_FAILURE_RETRY(waitpid(child, nullptr, 0));
    close(commands[1]);
    close(reports[0]);
    alarm(0);
    printf("%s Android 13 legacy process-group create/inherit/kill/cleanup\n", result ? "FAIL" : "PASS");
    return result;
}
