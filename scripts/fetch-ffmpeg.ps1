# Downloads a static Windows ffmpeg build into electron/build-resources/ffmpeg/
# so it can be bundled into the installer via electron-builder's extraResources.
# Run before `npm run dist` in electron/. Safe to re-run (skips if already present).

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$targetDir = Join-Path $repoRoot "electron\build-resources\ffmpeg"
$targetExe = Join-Path $targetDir "ffmpeg.exe"

if (Test-Path $targetExe) {
    Write-Host "ffmpeg already present at $targetExe, skipping download."
    exit 0
}

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

$zipUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$tempZip = Join-Path $env:TEMP "avrix-ffmpeg.zip"
$tempExtract = Join-Path $env:TEMP "avrix-ffmpeg-extract"

Write-Host "Downloading ffmpeg from $zipUrl ..."
Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip

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
