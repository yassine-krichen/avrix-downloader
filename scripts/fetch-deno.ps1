# Downloads a pinned Windows x64 deno.exe into electron/build-resources/deno/.
# yt-dlp needs an external JavaScript runtime to solve YouTube's signature
# challenges; the installer bundles deno so end users need nothing installed.
# Run before `npm run dist` in electron/. Safe to re-run (skips if present).
# To bump: change $version and $sha256 (shown on the GitHub release asset
# page https://github.com/denoland/deno/releases).

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

$version = "2.9.7"
$sha256 = "a0c3101b4158d1dfb7d6a78a7bf0f3de80c96bb423c152beec8beb22786f2238"

$repoRoot = Split-Path -Parent $PSScriptRoot
$targetDir = Join-Path $repoRoot "electron\build-resources\deno"
$targetExe = Join-Path $targetDir "deno.exe"

if (Test-Path $targetExe) {
    Write-Host "deno already present at $targetExe, skipping download."
    exit 0
}

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

$zipUrl = "https://github.com/denoland/deno/releases/download/v$version/deno-x86_64-pc-windows-msvc.zip"
$tempZip = Join-Path $env:TEMP "avrix-deno.zip"

Write-Host "Downloading deno $version from $zipUrl ..."
Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip

$actual = Get-Sha256 $tempZip
if ($actual -ne $sha256) {
    Remove-Item -Force $tempZip
    throw "deno checksum mismatch: expected $sha256, got $actual"
}

Expand-Archive -Path $tempZip -DestinationPath $targetDir -Force
Remove-Item -Force $tempZip

if (-not (Test-Path $targetExe)) {
    throw "deno.exe not found in downloaded archive"
}

Write-Host "deno ready at $targetExe"
