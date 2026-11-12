from pathlib import Path
import subprocess
root=Path('/root/t110-build/lineage20/build/soong')
p=root/'java/dexpreopt.go'; s=p.read_text()
s=s.replace('return inList(moduleName(ctx), dexpreopt.GetGlobalConfig(ctx).SpeedApps)', 'selected := ctx.Config().VendorConfig("t110").String("preopt_apex_name")\n\tinfo := ctx.Provider(android.ApexInfoProvider).(android.ApexInfo)\n\treturn selected != "" && inList(selected, info.InApexVariants) && inList(moduleName(ctx), dexpreopt.GetGlobalConfig(ctx).SpeedApps)')
start=s.index('\t\tinfo := ctx.Provider',s.index('func (d *dexpreopter) getInstallPath'))
end=s.index('\t\tapp :=',start)
s=s[:start]+'\t\tselected := ctx.Config().VendorConfig("t110").String("preopt_apex_name")\n'+s[end:]
s=s.replace('"apex", info.InApexVariants[0],','"apex", selected,')
p.write_text(s)
subprocess.run(['/root/t110-build/lineage20/prebuilts/go/linux-x86/bin/gofmt','-w',str(p)],check=True)
files=['java/dexpreopt.go','java/app.go','java/androidmk.go','apex/apex.go']
diff=subprocess.check_output(['git','-C',str(root),'diff','--binary','--']+files)
Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/patches/0042-soong-t110-flattened-apex-app-preopt.patch').write_bytes(diff)
print('Explicit product APEX name handles merged production/test module variations')
