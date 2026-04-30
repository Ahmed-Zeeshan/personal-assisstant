param([switch]$NoSetup)
$ErrorActionPreference = 'Stop'

$RepoUrl     = 'https://github.com/Ahmed-Zeeshan/personal-assisstant'
$VaHome      = if ($env:VA_HOME) { $env:VA_HOME } else { Join-Path $env:LOCALAPPDATA 'voice-assistant' }
$ConfigDir   = Join-Path $env:APPDATA 'voice-assistant'
$LauncherDir = Join-Path $env:LOCALAPPDATA 'Programs\voice-assistant'

function Say  ($m) { Write-Host ">>> $m" -ForegroundColor Magenta }
function Warn ($m) { Write-Host "!!! $m" -ForegroundColor Yellow  }
function Die  ($m) { Write-Host "xxx $m" -ForegroundColor Red; exit 1 }

if ($args[0] -eq '--uninstall') {
  Say "removing $VaHome"
  Remove-Item -Recurse -Force $VaHome -ErrorAction SilentlyContinue
  Remove-Item -Recurse -Force $LauncherDir -ErrorAction SilentlyContinue
  if (Test-Path $ConfigDir) {
    $ans = Read-Host "Also delete $ConfigDir (holds OAuth tokens & config)? [y/N]"
    if ($ans -match '^[yY]$') { Remove-Item -Recurse -Force $ConfigDir }
  }
  Say "uninstalled."
  exit 0
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) { Die "python not found. Install Python ≥3.11 from https://www.python.org/downloads/." }
$gitCmd    = Get-Command git    -ErrorAction SilentlyContinue
if (-not $gitCmd) { Die "git not found. pip needs git to install from $RepoUrl — install Git for Windows from https://git-scm.com/download/win." }

$pyVer = & python -c "import sys; print('%d.%d' % sys.version_info[:2])"
if (-not ($pyVer -in @('3.11','3.12','3.13','3.14'))) { Die "Python 3.11+ required (found $pyVer)." }

Say "installing into $VaHome"
New-Item -ItemType Directory -Force -Path $VaHome,$ConfigDir,$LauncherDir | Out-Null

Say "creating venv"
& python -m venv (Join-Path $VaHome '.venv')

$pip = Join-Path $VaHome '.venv\Scripts\pip.exe'
$exe = Join-Path $VaHome '.venv\Scripts\voice-assistant.exe'

Say "installing voice-assistant from $RepoUrl"
& $pip install --upgrade pip | Out-Null
$Extras = if ($env:VA_NO_DESKTOP -eq '1') { 'audio,gmail,web' } else { 'audio,gmail,web,desktop' }
& $pip install "voice-assistant[$Extras] @ git+$RepoUrl"

Say "creating launcher shortcut at $LauncherDir\voice-assistant.cmd"
@"
@echo off
"$exe" %*
"@ | Set-Content -Encoding ASCII (Join-Path $LauncherDir 'voice-assistant.cmd')

if (-not ($env:Path -split ';' | Where-Object { $_ -eq $LauncherDir })) {
  Warn "$LauncherDir is not on PATH. Add it via System → Environment Variables, or run:"
  Warn "  [Environment]::SetEnvironmentVariable('Path', `$env:Path + ';$LauncherDir', 'User')"
}

if ($env:SKIP_SETUP -ne '1' -and -not $NoSetup) {
  Say "running setup wizard"
  & $exe --setup --force
  if ($LASTEXITCODE -ne 0) {
    Warn "setup wizard exited non-zero; re-run later with: voice-assistant --setup"
  }
}

Say "done. Run: voice-assistant"
