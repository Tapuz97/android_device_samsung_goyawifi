$ErrorActionPreference = 'Stop'
$repo = 'Tapuz97/android_device_samsung_goyawifi'
$tag = 't110-android13-image-candidate-20261114'
$sourceBranch = 't110/android13-offline-audit-20261114'
$backup = '\\wsl.localhost\Ubuntu\root\t110-android13-audit\complete-candidate-backup'
$manifest = Get-Content -Raw -LiteralPath (Join-Path $backup 'backup-manifest.json') | ConvertFrom-Json
if ($manifest.status -ne 'PASS_LOCAL_BACKUP_READBACK') { throw 'Local backup gates have not passed.' }
$assets = @($manifest.files.name) + @('SHA256SUMS-image-candidate.txt', 'backup-manifest.json', 'README-CANDIDATE.md')
$hashes = @{}
foreach ($name in $assets) {
    $path = Join-Path $backup $name
    $hashes[$name] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
}
foreach ($file in $manifest.files) {
    if ($hashes[$file.name] -ne $file.sha256) { throw "Local asset hash mismatch: $($file.name)" }
}
function Get-CandidateRelease {
    $json = gh api "repos/$repo/releases?per_page=100"
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read backup releases.' }
    @($json | ConvertFrom-Json) | Where-Object tag_name -eq $tag
}
$release = Get-CandidateRelease
if (-not $release) {
    gh release create $tag --repo $repo --draft --target $sourceBranch --title 'SM-T110 Android 13 complete engineering candidate - offline checks only' --notes-file (Join-Path $backup 'README-CANDIDATE.md')
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create the separate candidate backup release.' }
    for ($attempt = 0; $attempt -lt 5 -and -not $release; $attempt++) {
        Start-Sleep -Seconds 2
        $release = Get-CandidateRelease
    }
}
if (-not $release) { throw 'New draft has not appeared in the API yet; retry this script.' }
if (-not $release.draft) { throw 'Refusing to modify a published release.' }
foreach ($name in $assets) {
    if (-not (@($release.assets.name) -contains $name)) {
        gh release upload $tag (Join-Path $backup $name) --repo $repo
        if ($LASTEXITCODE -ne 0) { throw "Upload failed: $name" }
    }
}
$readback = Join-Path $backup 'online-readback'
New-Item -ItemType Directory -Path $readback -Force | Out-Null
gh release download $tag --repo $repo --dir $readback --clobber
if ($LASTEXITCODE -ne 0) { throw 'Backup download/readback failed.' }
$verified = foreach ($name in $assets) {
    $path = Join-Path $readback $name
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $hashes[$name]) { throw "Online backup hash mismatch: $name" }
    [ordered]@{name=$name; bytes=(Get-Item -LiteralPath $path).Length; sha256=$actual}
}
$release = Get-CandidateRelease
$receipt = [ordered]@{
    status='PASS_ONLINE_DOWNLOAD_HASH_READBACK'; repository=$repo; tag=$tag
    release_id=$release.id; draft=$release.draft; source_branch=$sourceBranch
    verified_utc=(Get-Date).ToUniversalTime().ToString('o')
    assets=$verified; working14_backups_modified=$false; flashed=$false
}
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $backup 'online-backup-verification.json') -Encoding utf8
Write-Output "PASS: separate draft release $($release.id); all $($assets.Count) assets downloaded and hash-verified."
