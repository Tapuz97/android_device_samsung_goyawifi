param([string[]]$Versions = @('lineage20-rom-v1', 'lineage20-rom-v2'))
$ErrorActionPreference = 'Stop'
$artifactRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\artifacts')).Path
$archiveRoot = [System.IO.Path]::GetFullPath('D:\T110-artifacts')
New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null
$reportPath = Join-Path $PSScriptRoot '..\evidence\offline-v26\relocated-old-artifacts.json'
$records = @()
if (Test-Path -LiteralPath $reportPath) { $records = @(Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json) }
foreach ($version in $Versions) {
    if ($version -notmatch '^lineage20-rom-v[1-4]$') { throw 'Only old ROM versions1-4 are eligible' }
    $source = (Resolve-Path -LiteralPath (Join-Path $artifactRoot $version)).Path
    $target = [System.IO.Path]::GetFullPath((Join-Path $archiveRoot $version))
    if ((Split-Path $source -Parent) -ne $artifactRoot) { throw 'Source outside workspace artifacts' }
    if ((Split-Path $target -Parent) -ne $archiveRoot) { throw 'Target outside D archive' }
    if ((Get-Item -LiteralPath $source).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Unexpected source link' }
    if (Test-Path -LiteralPath $target) { throw "Target already exists: $target" }
    $files = @(Get-ChildItem -LiteralPath $source -Force)
    if ($files | Where-Object PSIsContainer) { throw 'Expected a flat artifact directory' }
    New-Item -ItemType Directory -Path $target | Out-Null
    $hashes = @{}
    foreach ($file in $files) {
        $hashes[$file.Name] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $target $file.Name)
    }
    foreach ($file in $files) {
        $copied = Join-Path $target $file.Name
        if ((Get-FileHash -LiteralPath $copied -Algorithm SHA256).Hash -ne $hashes[$file.Name]) { throw "Hash mismatch: $copied" }
    }
    # Only the files just copied and individually verified can be removed.
    foreach ($file in $files) { Remove-Item -LiteralPath $file.FullName }
    if (@(Get-ChildItem -LiteralPath $source -Force).Count -ne 0) { throw 'Source is not empty' }
    Remove-Item -LiteralPath $source
    New-Item -ItemType Junction -Path $source -Target $target | Out-Null
    $records += [pscustomobject]@{ source=$source; target=$target; verified_sha256=$hashes }
    Write-Output "RELOCATED_AND_VERIFIED $version"
}
$records | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $reportPath -Encoding utf8
Get-PSDrive -Name C,D | Select-Object Name,Free | ConvertTo-Json -Compress
