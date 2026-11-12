$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$evidence = Join-Path $project 'evidence'
$summary = Join-Path $evidence 'source-integrity-after-enclosure.json'
$trial = Get-Content -Raw -LiteralPath (Join-Path $evidence 'e-enclosure-replacement.json') | ConvertFrom-Json
$cutoff = ([datetimeoffset]$trial.checked_at).LocalDateTime
$deadline = (Get-Date).AddMinutes(45)
while (-not (Test-Path -LiteralPath $summary)) {
    if ((Get-Date) -gt $deadline) { throw 'Source integrity check did not finish within the wait window.' }
    if (-not (Test-Path -LiteralPath $trial.vhd)) { throw 'The build drive disappeared while the source check was running.' }
    Start-Sleep -Seconds 10
}
$audit = Get-Content -Raw -LiteralPath $summary | ConvertFrom-Json
if ($audit.failed_projects.Count) { throw 'Source integrity check found errors.' }
$linuxScripts = '/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110/scripts'
wsl -d T110Build -u root -- python3 "$linuxScripts/review_source_integrity.py" --after-enclosure
if ($LASTEXITCODE -ne 0) { throw 'Source difference review failed.' }
$storageErrors = @(Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$cutoff; Id=7,51,129,153,157} -ErrorAction SilentlyContinue |
    Where-Object { $_.ProviderName -in 'UASPStor','disk','Ntfs','stornvme','storahci' })
if ($storageErrors.Count) { throw 'Windows recorded new storage errors. Leave the build stopped.' }
wsl -d T110Build -u root -- python3 "$linuxScripts/resume_system_after_storage_check.py" --after-enclosure
exit $LASTEXITCODE
