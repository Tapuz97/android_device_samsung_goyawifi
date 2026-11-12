# Manual continuation after the automated C: pass encountered a directory lock.
$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Users\Gal\Documents\ChatGPT\Electronic Repair\SM-T110'
if ((Resolve-Path -LiteralPath $taskRoot).Path -ne $taskRoot) { throw 'Unexpected root' }
Set-Location -LiteralPath $taskRoot
[Environment]::CurrentDirectory = $taskRoot
$recordRoot = Join-Path $taskRoot 'backups/android13-before-lineage14-20261112'
$recordPath = Join-Path $recordRoot 'FINAL-ONLINE-VERIFIED.json'
if (-not (Test-Path -LiteralPath $recordPath)) {
    New-Item -ItemType Directory -Path $recordRoot -Force | Out-Null
    gh release download t110-development-backup-20261112 --repo Tapuz97/android_device_samsung_goyawifi --pattern FINAL-ONLINE-VERIFIED.json --dir $recordRoot
    if ($LASTEXITCODE -ne 0) { throw 'Could not retrieve verification record' }
}
if ((Get-FileHash -LiteralPath $recordPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne '99b4ca48608d40bdedf5219a4f79c6488d514ed61ecb3cf1f2fdf84e9b13ccd3') { throw 'Record hash mismatch' }
$proof = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
if (-not $proof.all_required_payloads_download_hash_verified -or -not $proof.full_restoration_archive_member_hash_verified -or $proof.assets.Count -ne 9) { throw 'Incomplete backup proof' }
$release = gh api repos/Tapuz97/android_device_samsung_goyawifi/releases/443063640 | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or -not $release.draft -or $release.published_at) { throw 'Private draft check failed' }
foreach ($required in $proof.assets) {
    $asset = @($release.assets | Where-Object {$_.name -eq $required.name})
    if ($asset.Count -ne 1 -or $asset[0].size -ne $required.bytes -or $asset[0].digest -ne ('sha256:' + $required.sha256) -or $asset[0].state -ne 'uploaded') { throw ('Backup mismatch: ' + $required.name) }
}
$keep = @('ACHIEVEMENTS.md','CLEANUP.md','CLEANUP-UBUNTU.md','CURRENT-STATUS.md','FEATURE-BACKLOG.md','FUNCTIONAL-CHECKLIST.md','LINEAGE14-GPU-AND-SLEEP-AUDIT.md','LINKS.md','ONLINE-BACKUP.md','REFERENCES.md','RESTORE.md','RESUME-NEXT.md')
$before = (Get-PSDrive C).Free
$pending = @()
$links = @(Get-ChildItem -LiteralPath $taskRoot -Recurse -Force -Directory | Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint})
foreach ($link in $links) {
    if (-not $link.FullName.StartsWith($taskRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Link escaped root' }
    try { Remove-Item -LiteralPath $link.FullName -Force -ErrorAction Stop } catch { $pending += $_.Exception.Message }
}
# Keep the helper and its verification record until every other removal succeeds.
$entries = @(Get-ChildItem -LiteralPath $taskRoot -Force | Where-Object {$_.Name -notin @('scripts','backups')})
foreach ($entry in $entries) {
    if (-not $entry.PSIsContainer -and $entry.Name -in $keep) { continue }
    if (-not $entry.FullName.StartsWith($taskRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Path escaped root' }
    try { Remove-Item -LiteralPath $entry.FullName -Recurse -Force -ErrorAction Stop } catch { $pending += $_.Exception.Message }
}
if ($pending.Count -eq 0) {
    Remove-Item -LiteralPath (Join-Path $taskRoot 'scripts') -Recurse -Force
    Remove-Item -LiteralPath (Join-Path $taskRoot 'backups') -Recurse -Force
}
$after = (Get-PSDrive C).Free
$remaining = @(Get-ChildItem -LiteralPath $taskRoot -Force | Where-Object {$_.PSIsContainer -or $_.Extension -ne '.md'})
$status = if ($remaining.Count -eq 0) {'COMPLETE'} else {'PENDING_FILE_LOCK'}
@"
# T110 cleanup result

Status: $status

All nine restoration payloads were downloaded and SHA256 verified before removal.
Source tags and restore instructions: LINKS.md, ONLINE-BACKUP.md and RESTORE.md.

The dedicated E: T110Build distro and obsolete E: build filesystem were removed.
Ubuntu /root/t110-build was removed, trimmed and its VHD compacted; Ubuntu itself remains.
This continuation removes only the named C: project payloads. It preserves the
informative Markdown records and does not follow D: junction targets.

C: free before/after this continuation: $before / $after bytes.

Pending errors: $($pending -join ' | ')
Remaining non-Markdown entries: $(($remaining | Select-Object -ExpandProperty Name) -join ', ')
"@ | Set-Content -LiteralPath (Join-Path $taskRoot 'CLEANUP.md')
Write-Host ('Cleanup {0}; C: free {1:N1} GiB' -f $status, ($after / 1GB))
if ($remaining.Count) { Write-Warning 'Close the window/process holding the listed folder and run this helper again.' }
