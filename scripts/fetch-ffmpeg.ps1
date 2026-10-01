# Downloads a pinned static Windows ffmpeg build into electron/build-resources/ffmpeg/
# so it can be bundled into the installer via electron-builder's extraResources.
# Run before `npm run dist` in electron/. Safe to re-run (skips if already present).
# To bump: change $version and $sha256 (published at
# https://github.com/GyanD/codexffmpeg/releases).

$ErrorActionPreference = "Stop"
# The progress bar slows Invoke-WebRequest by orders of magnitude in PS 5.
$ProgressPreference = "SilentlyContinue"

# .NET directly: Get-FileHash is unavailable when PSModulePath is polluted
# (e.g. launched from a pwsh 7 parent process).
function Get-Sha256([string]$path) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($path)
    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($stream)) -replace "-", "").ToLower()
    } finally {
        $stream.Dispose()
    }
}

$version = "9.0.2"
$sha256 = "60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba"

$repoRoot = Split-Path -Parent $PSScriptRoot
$targetDir = Join-Path $repoRoot "electron\build-resources\ffmpeg"
$targetExe = Join-Path $targetDir "ffmpeg.exe"

if (Test-Path $targetExe) {
    Write-Host "ffmpeg already present at $targetExe, skipping download."
    exit 0
}

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

$zipUrl = "https://github.com/GyanD/codexffmpeg/releases/download/$version/ffmpeg-$version-essentials_build.zip"
$tempZip = Join-Path $env:TEMP "avrix-ffmpeg.zip"
$tempExtract = Join-Path $env:TEMP "avrix-ffmpeg-extract"

Write-Host "Downloading ffmpeg $version from $zipUrl ..."
Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip

$actual = Get-Sha256 $tempZip
if ($actual -ne $sha256) {
    Remove-Item -Force $tempZip
    throw "ffmpeg checksum mismatch: expected $sha256, got $actual"
}

if (Test-Path $tempExtract) {
    Remove-Item -Recurse -Force $tempExtract
}
Expand-Archive -Path $tempZip -DestinationPath $tempExtract

$ffmpegExe = Get-ChildItem -Path $tempExtract -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
if (-not $ffmpegExe) {
    throw "ffmpeg.exe not found in downloaded archive"
}

Copy-Item $ffmpegExe.FullName -Destination $targetExe -Force

Remove-Item -Force $tempZip
Remove-Item -Recurse -Force $tempExtract

Write-Host "ffmpeg ready at $targetExe"
