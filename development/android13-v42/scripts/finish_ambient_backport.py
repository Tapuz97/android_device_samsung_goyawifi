"""Adapt the upstream ambient capability patch to the T110's 3.4 credential API."""
from pathlib import Path

ROOT = Path("/root/t110-build/kernel-platform")


def replace(path, old, new):
    file = ROOT / path
    text = file.read_text()
    assert text.count(old) == 1, (path, old)
    file.write_text(text.replace(old, new))


replace("fs/proc/array.c", "\tcap_bset\t= cred->cap_bset;",
        "\tcap_bset\t= cred->cap_bset;\n\tcap_ambient = cred->cap_ambient;")
replace("fs/proc/array.c", '\trender_cap_t(m, "CapBnd:\\t", &cap_bset);',
        '\trender_cap_t(m, "CapBnd:\\t", &cap_bset);\n\trender_cap_t(m, "CapAmb:\\t", &cap_ambient);')
replace("include/linux/prctl.h", "#endif /* _LINUX_PRCTL_H */", """#define PR_CAP_AMBIENT 47
# define PR_CAP_AMBIENT_IS_SET 1
# define PR_CAP_AMBIENT_RAISE 2
# define PR_CAP_AMBIENT_LOWER 3
# define PR_CAP_AMBIENT_CLEAR_ALL 4

#endif /* _LINUX_PRCTL_H */""")
replace("kernel/user_namespace.c", "\tnew->user = root_user;",
        "\tnew->user = root_user;\n\tcap_clear(new->cap_ambient);")
replace("security/commoncap.c", "\tbool effective, has_cap = false;",
        "\tbool effective, has_cap = false, is_setid;")
replace("security/commoncap.c", """\tif ((new->euid != old->uid ||
\t     new->egid != old->gid ||
\t     !cap_issubset(new->cap_permitted, old->cap_permitted)) &&""",
        """\tis_setid = new->euid != old->uid || new->egid != old->gid;
\tif ((is_setid ||
\t     !cap_issubset(new->cap_permitted, old->cap_permitted)) &&""")
replace("security/commoncap.c", """\tif (has_cap || is_setid)
\t\tcap_clear(new->cap_ambient);""", """\tif (has_cap || is_setid)
\t\tcap_clear(new->cap_ambient);
\telse
\t\tnew->cap_ambient = old->cap_ambient;""")
replace("security/commoncap.c", "\tif (!cap_isclear(new->cap_effective)) {",
        "\tif (!cap_issubset(new->cap_effective, new->cap_ambient)) {")
replace("security/commoncap.c", "\t\tif (!cap_isclear(cred->cap_permitted))",
        "\t\tif (!cap_issubset(cred->cap_permitted, cred->cap_ambient))")
replace("security/commoncap.c", """\t    (new->uid != 0 && new->euid != 0 && new->suid != 0) &&
\t    !issecure(SECURE_KEEP_CAPS)) {
\t\tcap_clear(new->cap_permitted);
\t\tcap_clear(new->cap_effective);
\t}""", """\t    (new->uid != 0 && new->euid != 0 && new->suid != 0)) {
\t\tif (!issecure(SECURE_KEEP_CAPS)) {
\t\t\tcap_clear(new->cap_permitted);
\t\t\tcap_clear(new->cap_effective);
\t\t}
\t\tcap_clear(new->cap_ambient);
\t}""")
replace("security/commoncap.c", """\tdefault:
\t\t/* No functionality available - continue with default */""", """\tcase PR_CAP_AMBIENT:
\t\terror = -EINVAL;
\t\tif (arg2 == PR_CAP_AMBIENT_CLEAR_ALL) {
\t\t\tif (arg3 | arg4 | arg5)
\t\t\t\tgoto error;
\t\t\tcap_clear(new->cap_ambient);
\t\t\tgoto changed;
\t\t}
\t\tif (!cap_valid(arg3) || arg4 || arg5)
\t\t\tgoto error;
\t\tswitch (arg2) {
\t\tcase PR_CAP_AMBIENT_IS_SET:
\t\t\terror = !!cap_raised(new->cap_ambient, arg3);
\t\t\tgoto no_change;
\t\tcase PR_CAP_AMBIENT_RAISE:
\t\t\terror = -EPERM;
\t\t\tif (!cap_raised(new->cap_permitted, arg3) ||
\t\t\t    !cap_raised(new->cap_inheritable, arg3) ||
\t\t\t    issecure(SECURE_NO_CAP_AMBIENT_RAISE))
\t\t\t\tgoto error;
\t\t\tcap_raise(new->cap_ambient, arg3);
\t\t\tgoto changed;
\t\tcase PR_CAP_AMBIENT_LOWER:
\t\t\tcap_lower(new->cap_ambient, arg3);
\t\t\tgoto changed;
\t\tdefault:
\t\t\tgoto error;
\t\t}

\tdefault:
\t\t/* No functionality available - continue with default */""")
replace("include/linux/securebits.h", "#define SECURE_ALL_BITS", """#define SECURE_NO_CAP_AMBIENT_RAISE 6
#define SECURE_NO_CAP_AMBIENT_RAISE_LOCKED 7
#define SECBIT_NO_CAP_AMBIENT_RAISE (issecure_mask(SECURE_NO_CAP_AMBIENT_RAISE))
#define SECBIT_NO_CAP_AMBIENT_RAISE_LOCKED (issecure_mask(SECURE_NO_CAP_AMBIENT_RAISE_LOCKED))

#define SECURE_ALL_BITS""")
replace("include/linux/securebits.h", "\t\t\t\t issecure_mask(SECURE_KEEP_CAPS))",
        "\t\t\t\t issecure_mask(SECURE_KEEP_CAPS) | \\\n\t\t\t\t issecure_mask(SECURE_NO_CAP_AMBIENT_RAISE))")
print("Ambient capability patch adapted")
