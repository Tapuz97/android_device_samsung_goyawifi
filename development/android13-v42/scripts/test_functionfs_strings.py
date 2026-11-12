"""ASan regression using the actual kernel parser, before and after patch 0012."""
import os
import subprocess
from pathlib import Path

base = Path('/root/t110-build')
source = base / 'kernel-binder-modern'
project = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
dest = project / 'artifacts/functionfs-regression'
dest.mkdir(exist_ok=True)
work = base / 'functionfs-regression'
work.mkdir(exist_ok=True)
relative = 'drivers/usb/gadget/f_fs.c'
before = subprocess.check_output(['git', '-C', str(source), 'show', 'HEAD:' + relative], text=True)
after = (source / relative).read_text()
start = 'static int __ffs_data_got_strings(struct ffs_data *ffs,\n'
def parser(text):
    begin = text.index(start)
    end = text.index('\n/* Events handling', begin)
    return text[begin:end]
prefix = r'''
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
typedef uint32_t u32;
#define ENTER() ((void)0)
#define unlikely(x) (x)
#define likely(x) (x)
#define GFP_KERNEL 0
#define FUNCTIONFS_STRINGS_MAGIC 2
#define kmalloc(n, flags) malloc(n)
#define kfree(p) free(p)
struct usb_string { uint8_t id; const char *s; };
struct usb_gadget_strings { uint16_t language; struct usb_string *strings; };
struct ffs_data { unsigned short strings_count; struct usb_gadget_strings **stringtabs; char *raw_strings; };
static uint32_t get_unaligned_le32(const void *p) { const uint8_t *b=p; return b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24; }
static uint16_t get_unaligned_le16(const void *p) { const uint8_t *b=p; return b[0]|(uint16_t)b[1]<<8; }
'''
suffix = r'''
static char *payload(int malformed, size_t *len) {
    const char string[] = "ADB Interface";
    *len = 16 + 2 + sizeof(string);
    char *p = calloc(1, *len);
    uint32_t header[] = {2, (uint32_t)*len, 1, 1};
    memcpy(p, header, sizeof(header)); p[16]=9; p[17]=4;
    memcpy(p+18, string, sizeof(string));
    if (malformed) p[*len-1]='X';
    return p;
}
int main(void) {
    for (int malformed=0; malformed<2; ++malformed) {
        struct ffs_data ffs = {.strings_count=1}; size_t len;
        char *p=payload(malformed, &len);
        int rc=__ffs_data_got_strings(&ffs, p, len);
        if (malformed) { assert(rc == -EINVAL); assert(!ffs.stringtabs); continue; }
        assert(rc == 0 && ffs.stringtabs && !ffs.stringtabs[1]);
        assert(ffs.stringtabs[0]->language == 0x409);
        struct usb_string *s=ffs.stringtabs[0]->strings;
        assert(!strcmp(s[0].s, "ADB Interface") && !s[1].s);
        s[0].id=5; /* Same table walk/write that failed in functionfs_bind. */
        free(ffs.stringtabs); free(ffs.raw_strings);
    }
    puts("PASS actual FunctionFS parser: valid ADB strings, bind table walk, malformed input cleanup");
}
'''
for name, text in [('before', before), ('after', after)]:
    c = work / (name + '.c')
    c.write_text(prefix + parser(text) + suffix)
    subprocess.run(['gcc', '-g', '-O1', '-fsanitize=address', '-fno-omit-frame-pointer', str(c), '-o', str(work / name)], check=True)
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:halt_on_error=1')
    result = subprocess.run([str(work / name)], text=True, capture_output=True, env=env)
    log = result.stdout + result.stderr
    (dest / (name + '.log')).write_text(log)
    (dest / (name + '.c')).write_text(c.read_text())
    if name == 'before':
        assert result.returncode != 0 and 'heap-use-after-free' in log, log
        print('PASS original parser reproduces heap-use-after-free')
    else:
        assert result.returncode == 0 and 'PASS actual' in log, log
        print(log.strip())
