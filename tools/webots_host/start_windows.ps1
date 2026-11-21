# Run by start_windows.cmd: Webots natively on Windows + the ROS 2 stack in
# Docker (HOST_PLATFORM=windows), stopped together on exit or Ctrl+C.
param([string]$World)

$repo = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $repo

# World: argument, else WORLD from .env (the file docker compose reads).
$envFile = Join-Path $repo '.env'
if (-not $World -and (Test-Path $envFile)) {
    $match = Select-String -Path $envFile -Pattern '^\s*WORLD\s*=\s*(\S+)' | Select-Object -First 1
    if ($match) { $World = $match.Matches[0].Groups[1].Value }
}
if (-not $World) { $World = 'mine_test_arena.wbt' }

# cmd /c keeps docker's stderr out of PowerShell's error stream.
function Test-Docker { cmd /c 'docker info >nul 2>&1'; return $LASTEXITCODE -eq 0 }
if (-not (Test-Docker)) {
    Write-Host 'Starting Docker Desktop...'
    Start-Process "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
    $deadline = (Get-Date).AddMinutes(3)
    while (-not (Test-Docker)) {
        if ((Get-Date) -gt $deadline) { Write-Error 'Docker Desktop did not start.'; exit 1 }
        Start-Sleep -Seconds 3
    }
}

function Stop-Webots { Get-Process webots, webots-bin -ErrorAction SilentlyContinue | Stop-Process -Force }

# Start from a clean state: no Webots or stack left over from an earlier run.
$env:HOST_PLATFORM = 'windows'
Stop-Webots
docker compose stop sim 2>&1 | Out-Null

$webots = Start-Process -FilePath "$repo\tools\webots_host\start_webots.cmd" -ArgumentList $World `
    -WindowStyle Minimized -PassThru
Start-Sleep -Seconds 3
if ($webots.HasExited -and $webots.ExitCode -ne 0) {
    Write-Error "Webots did not start (world '$World'?). Run tools\webots_host\start_webots.cmd $World to see why."
    exit 1
}

try {
    # The container's controllers retry until Webots has loaded the world.
    docker compose up sim
} finally {
    docker compose stop sim 2>&1 | Out-Null
    Stop-Webots
}
