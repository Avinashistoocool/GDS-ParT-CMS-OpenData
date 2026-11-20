# Push every kernel under kaggle/ to Kaggle.
# Username: $env:KAGGLE_USERNAME, else `kaggle config view`, else ~/.kaggle/kaggle.json.
param([string]$Only = "")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$user = $env:KAGGLE_USERNAME
if (-not $user) {
    $line = kaggle config view 2>$null | Select-String -Pattern "username:\s*(\S+)"
    if ($line) { $user = $line.Matches[0].Groups[1].Value }
}
if (-not $user) {
    $kj = Join-Path $env:USERPROFILE ".kaggle\kaggle.json"
    if (Test-Path $kj) { $user = (Get-Content $kj -Raw | ConvertFrom-Json).username }
}
if (-not $user) { throw "Kaggle username not found (set KAGGLE_USERNAME or run kaggle auth)" }
Write-Host "Kaggle user: $user"
Get-ChildItem (Join-Path $root "kaggle") -Directory | Where-Object { -not $Only -or $_.Name -eq $Only } | ForEach-Object {
    $meta = Join-Path $_.FullName "kernel-metadata.json"
    if (-not (Test-Path $meta)) { return }
    $j = Get-Content $meta -Raw | ConvertFrom-Json
    $slug = ($j.id -split "/")[1]
    $j.id = "$user/$slug"
    $j | ConvertTo-Json -Depth 5 | Set-Content $meta -Encoding ascii
    Write-Host "Pushing $($j.id) ..."
    kaggle kernels push -p $_.FullName
    Write-Host "https://www.kaggle.com/code/$user/$slug"
}
