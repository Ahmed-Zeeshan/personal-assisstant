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
if (-not $pythonCmd) { Die "python not found. Install Python ≥3.10 from https://www.python.org/downloads/." }

$pyVer = & python -c "import sys; print('%d.%d' % sys.version_info[:2])"
if (-not ($pyVer -in @('3.10','3.11','3.12','3.13','3.14'))) { Die "Python 3.10+ required (found $pyVer)." }

Say "installing into $VaHome"
New-Item -ItemType Directory -Force -Path $VaHome,$ConfigDir,$LauncherDir | Out-Null

Say "creating venv"
& python -m venv (Join-Path $VaHome '.venv')

$pip = Join-Path $VaHome '.venv\Scripts\pip.exe'
$exe = Join-Path $VaHome '.venv\Scripts\voice-assistant.exe'

Say "installing voice-assistant from $RepoUrl"
& $pip install --upgrade pip | Out-Null
& $pip install "voice-assistant[audio,gmail] @ git+$RepoUrl"

Say "creating launcher shortcut at $LauncherDir\voice-assistant.cmd"
@"
@echo off
"$exe" %*
"@ | Set-Content -Encoding ASCII (Join-Path $LauncherDir 'voice-assistant.cmd')

if (-not ($env:Path -split ';' | Where-Object { $_ -eq $LauncherDir })) {
  Warn "$LauncherDir is not on PATH. Add it via System → Environment Variables, or run:"
  Warn "  [Environment]::SetEnvironmentVariable('Path', `$env:Path + ';$LauncherDir', 'User')"
}

Say "done. Set your API key in $ConfigDir\.env, then run: voice-assistant"
