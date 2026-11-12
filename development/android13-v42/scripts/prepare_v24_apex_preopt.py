"""Opt selected apps in flattened APEXes into the existing ART preopt mechanism."""
from pathlib import Path
import subprocess
tree=Path('/root/t110-build/lineage20/build/soong')
project=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110')

def edit(name,old,new):
    p=tree/name; s=p.read_text(); assert s.count(old)==1,(name,old)
    p.write_text(s.replace(old,new,1))

edit('java/dexpreopt.go', 'func (d *dexpreopter) dexpreoptDisabled(ctx android.BaseModuleContext) bool {',
'''// The T110 cannot JIT. Opt only selected startup apps in flattened APEXes into
// precompilation. Ordinary/updatable APEX builds keep their existing behavior.
func (d *dexpreopter) preoptFlattenedApexApp(ctx android.BaseModuleContext) bool {
	if !ctx.Config().FlattenApex() || !ctx.Config().VendorConfig("t110").Bool("preopt_flattened_apex_apps") || !isApexVariant(ctx) {
		return false
	}
	if _, ok := ctx.Module().(*AndroidApp); !ok {
		return false
	}
	selected := ctx.Config().VendorConfig("t110").String("preopt_apex_name")
	info := ctx.Provider(android.ApexInfoProvider).(android.ApexInfo)
	return selected != "" && inList(selected, info.InApexVariants) && inList(moduleName(ctx), dexpreopt.GetGlobalConfig(ctx).SpeedApps)
}

func (d *dexpreopter) dexpreoptDisabled(ctx android.BaseModuleContext) bool {''')
edit('java/dexpreopt.go',
     'if !isApexSystemServerJar || ctx.Config().UnbundledBuild() {',
     'if (!isApexSystemServerJar && !d.preoptFlattenedApexApp(ctx)) || ctx.Config().UnbundledBuild() {')
edit('java/dexpreopt.go',
'''ctx android.ModuleContext, defaultInstallPath android.InstallPath) android.InstallPath {
	global := dexpreopt.GetGlobalConfig(ctx)''',
'''ctx android.ModuleContext, defaultInstallPath android.InstallPath) android.InstallPath {
	if d.preoptFlattenedApexApp(ctx) {
		selected := ctx.Config().VendorConfig("t110").String("preopt_apex_name")
		app := ctx.Module().(*AndroidApp)
		dir := "app"
		if app.Privileged() { dir = "priv-app" }
		name := app.InstallApkName()
		// Match apexFileForAndroidApp's versioned directory and runtime /apex path.
		return android.PathForModuleInPartitionInstall(ctx, "", "apex", selected,
			dir, name+"@"+ctx.Config().BuildId(), name+".apk")
	}
	global := dexpreopt.GetGlobalConfig(ctx)''')
edit('java/dexpreopt.go',
'''	isApexSystemServerJar := global.AllApexSystemServerJars(ctx).ContainsJar(moduleName(ctx))

	for _, install := range dexpreoptRule.Installs() {''',
'''	isApexSystemServerJar := global.AllApexSystemServerJars(ctx).ContainsJar(moduleName(ctx))
	hasApexInstalls := isApexSystemServerJar || d.preoptFlattenedApexApp(ctx)

	for _, install := range dexpreoptRule.Installs() {''')
edit('java/dexpreopt.go', '\t\tif isApexSystemServerJar {\n\t\t\t// APEX variants',
     '\t\tif hasApexInstalls {\n\t\t\t// APEX variants')
edit('java/dexpreopt.go', '\tif !isApexSystemServerJar {\n\t\td.builtInstalled',
     '\tif !hasApexInstalls {\n\t\td.builtInstalled')
edit('java/app.go', '\ta.dexpreopter.installPath = a.installPath(ctx)',
     '\ta.dexpreopter.installPath = a.dexpreopter.getInstallPath(ctx, a.installPath(ctx))')
edit('java/androidmk.go',
'''func (app *AndroidApp) AndroidMkEntries() []android.AndroidMkEntries {
	if app.hideApexVariantFromMake || app.IsHideFromMake() {''',
'''func (app *AndroidApp) AndroidMkEntries() []android.AndroidMkEntries {
	if app.hideApexVariantFromMake {
		entries := app.dexpreopter.AndroidMkEntriesForApex()
		return append(entries, android.AndroidMkEntries{Disabled: true})
	}
	if app.IsHideFromMake() {''')
edit('apex/apex.go',
'''af := newApexFile(ctx, fileToCopy, aapp.BaseModuleName(), dirInApex, app, aapp)
	af.jacocoReportClassesFile''',
'''af := newApexFile(ctx, fileToCopy, aapp.BaseModuleName(), dirInApex, app, aapp)
	if dexpreopter, ok := aapp.(java.DexpreopterInterface); ok {
		for _, install := range dexpreopter.DexpreoptBuiltInstalledForApex() {
			af.requiredModuleNames = append(af.requiredModuleNames, install.FullModuleName())
		}
	}
	af.jacocoReportClassesFile''')
files=['java/dexpreopt.go','java/app.go','java/androidmk.go','apex/apex.go']
subprocess.run(['/root/t110-build/lineage20/prebuilts/go/linux-x86/bin/gofmt','-w']+
               [str(tree/f) for f in files],check=True)
subprocess.run(['git','-C',str(tree),'diff','--check'],check=True)
# This checkout also contains the older host GC patch; do not duplicate it here.
diff=subprocess.check_output(['git','-C',str(tree),'diff','--binary','--']+files)
(project/'patches/0042-soong-t110-flattened-apex-app-preopt.patch').write_bytes(diff)
print('Flattened APEX startup-app preopt integrated with normal system OAT installation')
