"""Apply the GOYA touchscreen charging-flag correction to the active kernel tree."""
from pathlib import Path
import difflib, hashlib, json

p = Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')
b = Path('/root/t110-build')
name = 'drivers/input/touchscreen/bt532_ts.c'
source = b/'kernel-display-i2c'/name
old = source.read_text()
before = '''\tpr_info("[TSP]: %s\\n", __func__);
#if defined(CONFIG_SPA) || defined(CONFIG_SPA_LPM_MODE)
\tif (!spa_lpm_charging_mode_get())'''
after = '''\tpr_info("[TSP]: %s\\n", __func__);
#if defined(CONFIG_MACH_GOYA)
\t/* The GOYA custom ROM starts Android even when the bootloader passes
\t * lpcharge=1. Keep input available in that boot path as well. */
\treturn i2c_add_driver(&bt532_ts_driver);
#else
#if defined(CONFIG_SPA) || defined(CONFIG_SPA_LPM_MODE)
\tif (!spa_lpm_charging_mode_get())'''
tail = '''\telse
\t\treturn 0;
}

static void __exit bt532_ts_exit'''
newtail = '''\telse
\t\treturn 0;
#endif
}

static void __exit bt532_ts_exit'''
e=p/'evidence/offline-v38';e.mkdir(exist_ok=True)
if 'The GOYA custom ROM starts Android' not in old:
    assert old.count(before)==1 and old.count(tail)==1
    new=old.replace(before,after).replace(tail,newtail)
    diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    (p/'patches/0074-kernel-goya-touch-in-charger-boot.patch').write_text(diff)
    source.write_text(new)
    (e/'source.json').write_text(json.dumps(dict(source=name,before_sha256=hashlib.sha256(old.encode()).hexdigest(),after_sha256=hashlib.sha256(new.encode()).hexdigest(),reason='lpcharge=1 skipped driver registration while custom Android boots fully',scope='CONFIG_MACH_GOYA only'),indent=2)+'\n')
else:
    record=json.loads((e/'source.json').read_text())
    assert hashlib.sha256(old.encode()).hexdigest()==record['after_sha256']
print('TOUCH_CHARGER_SOURCE_READY')
