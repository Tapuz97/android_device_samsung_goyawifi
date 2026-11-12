$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Users\Gal\Documents\ChatGPT\Electronic Repair\SM-T110'
$expectedDriveRoot = 'E:\T110-build'
$keepMarkdown = @('ACHIEVEMENTS.md','CLEANUP.md','CLEANUP-UBUNTU.md','CURRENT-STATUS.md','FEATURE-BACKLOG.md','FUNCTIONAL-CHECKLIST.md','LINEAGE14-GPU-AND-SLEEP-AUDIT.md','LINKS.md','ONLINE-BACKUP.md','REFERENCES.md','RESTORE.md','RESUME-NEXT.md')
if ((Resolve-Path -LiteralPath $taskRoot).Path -ne $taskRoot) { throw 'Unexpected project root' }
$proofPath = Join-Path $taskRoot 'backups/android13-before-lineage14-20261112/FINAL-ONLINE-VERIFIED.json'
$proof = Get-Content -LiteralPath $proofPath -Raw | ConvertFrom-Json
if (-not $proof.all_required_payloads_download_hash_verified -or -not $proof.full_restoration_archive_member_hash_verified) { throw 'Online backup is incomplete' }
$current = gh api repos/Tapuz97/android_device_samsung_goyawifi/releases/443063640 | ConvertFrom-Json
if (-not $current.draft -or $current.published_at) { throw 'Expected a private unpublished draft' }
foreach ($required in $proof.assets) {
    $asset = @($current.assets | Where-Object {$_.name -eq $required.name})
    if ($asset.Count -ne 1 -or $asset[0].size -ne $required.bytes -or $asset[0].digest -ne ('sha256:' + $required.sha256) -or $asset[0].state -ne 'uploaded') { throw ('Remote asset mismatch: ' + $required.name) }
}
$beforeC = (Get-PSDrive C).Free
$beforeE = (Get-PSDrive E).Free
wsl.exe -d Ubuntu -- python3 -c "from pathlib import Path; assert not Path('/root/t110-build').exists(), 'Ubuntu task tree still present'"
if ($LASTEXITCODE -ne 0) { throw 'Ubuntu task cleanup must finish first; host files retained' }
$buildDistro = @(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' | ForEach-Object {Get-ItemProperty -LiteralPath $_.PSPath} | Where-Object {$_.DistributionName -eq 'T110Build'})
if ($buildDistro.Count -gt 1) { throw 'Ambiguous distro' }
if ($buildDistro.Count -eq 1) {
    if ([IO.Path]::GetFullPath($buildDistro[0].BasePath).TrimEnd('\') -ne 'E:\T110-build\WSL') { throw 'Distro is outside the dedicated task root' }
    wsl.exe -d T110Build -- sync
    if ($LASTEXITCODE -ne 0) { throw 'Build filesystem did not flush' }
    wsl.exe --terminate T110Build
    if ($LASTEXITCODE -ne 0) { throw 'Build distro did not stop' }
    wsl.exe --unregister T110Build
    if ($LASTEXITCODE -ne 0) { throw 'Build distro was not removed' }
}
$ubuntuDistro = @(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' | ForEach-Object {Get-ItemProperty -LiteralPath $_.PSPath} | Where-Object {$_.DistributionName -eq 'Ubuntu'})
if ($ubuntuDistro.Count -ne 1 -or $ubuntuDistro[0].BasePath -ne 'C:\Users\Gal\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState') { throw 'Unexpected Ubuntu disk location' }
wsl.exe --terminate Ubuntu
if ($LASTEXITCODE -ne 0) { throw 'Ubuntu did not stop before compaction' }
# WSL3.0.5 advertises this built-in command; no unsafe sparse flags or admin workaround.
wsl.exe --manage Ubuntu --compact
$compactExit = $LASTEXITCODE
if (Test-Path -LiteralPath $expectedDriveRoot) {
    $driveRoot = (Resolve-Path -LiteralPath $expectedDriveRoot).Path
    if ($driveRoot -ne 'E:\T110-build' -or (((Get-Item -LiteralPath $driveRoot).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) { throw 'Unexpected E path' }
    foreach ($entry in Get-ChildItem -LiteralPath $driveRoot -Force) {
        $resolved = $entry.FullName
        if (-not $resolved.StartsWith('E:\T110-build\', [StringComparison]::OrdinalIgnoreCase)) { throw 'E path escaped' }
        if ($entry.Name -eq 'README.md' -and -not $entry.PSIsContainer) { continue }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
    '# T110 build files removed after verified online backup' | Set-Content -LiteralPath (Join-Path $driveRoot 'README.md')
    'See C:\Users\Gal\Documents\ChatGPT\Electronic Repair\SM-T110\LINKS.md and ONLINE-BACKUP.md. No other E: folder was removed.' | Add-Content -LiteralPath (Join-Path $driveRoot 'README.md')
}
# Remove junctions themselves first; never follow their D: or other targets.
$junctions = Get-ChildItem -LiteralPath $taskRoot -Recurse -Force -Directory | Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}
foreach ($link in $junctions) {
    if (-not $link.FullName.StartsWith($taskRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Link path escaped' }
    Remove-Item -LiteralPath $link.FullName -Force
}
foreach ($entry in Get-ChildItem -LiteralPath $taskRoot -Force) {
    if (-not $entry.PSIsContainer -and $entry.Extension -eq '.md' -and $entry.Name -in $keepMarkdown) { continue }
    $resolved = $entry.FullName
    if (-not $resolved.StartsWith($taskRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'C path escaped' }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
$remaining = @(Get-ChildItem -LiteralPath $taskRoot -Force | Where-Object {$_.PSIsContainer -or $_.Extension -ne '.md'})
if ($remaining.Count) { throw 'Non-Markdown files remain' }
$afterC = (Get-PSDrive C).Free
$afterE = (Get-PSDrive E).Free
@"
# Final T110 cleanup

Completed after authenticated online download/SHA256 verification of every required payload.

- C task directory contains only informational Markdown.
- Ubuntu /root/t110-build removed; Ubuntu itself retained.
- Dedicated T110Build distro and E:\T110-build payloads removed; E has only its Markdown pointer.
- Other projects, apps, files, disks and D: targets were not removed.
- C free before/after: $beforeC / $afterC bytes.
- E free before/after: $beforeE / $afterE bytes.
- Built-in Ubuntu VHD compaction exit code: $compactExit.
- See LINKS.md, ONLINE-BACKUP.md, RESTORE.md and CLEANUP-UBUNTU.md.
"@ | Set-Content -LiteralPath (Join-Path $taskRoot 'CLEANUP.md')
Get-PSDrive C,E | Format-List Name,Free
