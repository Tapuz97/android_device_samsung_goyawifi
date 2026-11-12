from pathlib import Path
import subprocess
p=Path(__file__).resolve().parents[1];e=p/'evidence/hardware-v35/bluetooth-source';e.mkdir(exist_ok=True)
for name in ['bt_drv.h','bt_init.c','bt_main.c','bt_sdiommc.c','hci_wrapper.h','mbt_char.h','mbt_char.c']:
 f='/root/t110-build/kernel-display-i2c/drivers/marvell/sd8787/mbtc_src/bt/'+name
 r=subprocess.run(['wsl.exe','-d','Ubuntu','--','cat',f],capture_output=True,timeout=45);assert r.returncode==0
 (e/name).write_bytes(r.stdout);print(name,len(r.stdout))
