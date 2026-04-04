param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("list", "start", "start-all", "stop", "stop-all", "status")]
    [string]$Action,

    [Parameter(Position = 1)]
    [string[]]$Profiles
)

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$ProfilesDir = Join-Path $ProjectRoot "profiles"
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$PidDir = Join-Path $ProjectRoot ".bot_pids"
$LogDir = Join-Path $ProjectRoot ".bot_logs"

New-Item -ItemType Directory -Path $PidDir -Force | Out-Null
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

if (-not (Test-Path $PythonExe)) {
    throw "Python not found: $PythonExe"
}

function Get-AvailableProfiles {
    Get-ChildItem -Path $ProfilesDir -Filter "*.py" |
        Where-Object { $_.BaseName -notin @("__init__", "template_client") } |
        Select-Object -ExpandProperty BaseName
}

function Get-PidPath([string]$Profile) {
    Join-Path $PidDir ("{0}.pid" -f $Profile)
}

function Get-LogPath([string]$Profile) {
    Join-Path $LogDir ("{0}.log" -f $Profile)
}

function Get-RunningProcess([string]$Profile) {
    $pidPath = Get-PidPath $Profile
    if (-not (Test-Path $pidPath)) {
        return $null
    }

    $rawPid = (Get-Content $pidPath -Raw).Trim()
    if (-not $rawPid) {
        Remove-Item $pidPath -Force -ErrorAction SilentlyContinue
        return $null
    }

    try {
        $proc = Get-Process -Id ([int]$rawPid) -ErrorAction Stop
        return $proc
    }
    catch {
        Remove-Item $pidPath -Force -ErrorAction SilentlyContinue
        return $null
    }
}

function Ensure-ProfileExists([string]$Profile) {
    $profilePath = Join-Path $ProfilesDir ("{0}.py" -f $Profile)
    if (-not (Test-Path $profilePath)) {
        throw "Profile not found: $Profile (expected file: $profilePath)"
    }
}

function Resolve-TargetProfiles([string[]]$Requested, [bool]$UseAllIfEmpty) {
    if ($Requested -and $Requested.Count -gt 0) {
        return $Requested
    }

    if ($UseAllIfEmpty) {
        return @(Get-AvailableProfiles)
    }

    return @()
}

function Start-Bot([string]$Profile) {
    Ensure-ProfileExists $Profile

    $running = Get-RunningProcess $Profile
    if ($running) {
        Write-Host ("[ALREADY RUNNING] {0} (PID {1})" -f $Profile, $running.Id) -ForegroundColor Yellow
        return
    }

    $logPath = Get-LogPath $Profile
    $profileEscaped = $Profile.Replace("'", "''")
    $projectEscaped = $ProjectRoot.Replace("'", "''")
    $pythonEscaped = $PythonExe.Replace("'", "''")
    $logEscaped = $logPath.Replace("'", "''")

    $command = "Set-Location -LiteralPath '$projectEscaped'; `$env:AUTOBOT_PROFILE='$profileEscaped'; & '$pythonEscaped' '.\\main.py' *>> '$logEscaped'"

    $proc = Start-Process -FilePath "powershell.exe" `
        -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $command `
        -PassThru `
        -WindowStyle Minimized

    Set-Content -Path (Get-PidPath $Profile) -Value $proc.Id

    Write-Host ("[STARTED] {0} (PID {1})" -f $Profile, $proc.Id) -ForegroundColor Green
    Write-Host ("log: {0}" -f $logPath)
}

function Stop-Bot([string]$Profile) {
    $running = Get-RunningProcess $Profile
    if (-not $running) {
        Write-Host ("[NOT RUNNING] {0}" -f $Profile) -ForegroundColor Yellow
        return
    }

    Stop-Process -Id $running.Id -Force
    Remove-Item (Get-PidPath $Profile) -Force -ErrorAction SilentlyContinue
    Write-Host ("[STOPPED] {0}" -f $Profile) -ForegroundColor Green
}

function Print-Status([string[]]$AllProfiles) {
    foreach ($profile in $AllProfiles) {
        $running = Get-RunningProcess $profile
        if ($running) {
            Write-Host ("[RUNNING] {0} (PID {1})" -f $profile, $running.Id) -ForegroundColor Green
        }
        else {
            Write-Host ("[STOPPED] {0}" -f $profile) -ForegroundColor DarkYellow
        }
    }
}

$allProfiles = @(Get-AvailableProfiles)
if (-not $allProfiles -or $allProfiles.Count -eq 0) {
    throw "No profiles found in $ProfilesDir"
}

switch ($Action) {
    "list" {
        Write-Host "Available profiles:" -ForegroundColor Cyan
        $allProfiles | ForEach-Object { Write-Host "- $_" }
    }

    "start" {
        $targets = Resolve-TargetProfiles -Requested $Profiles -UseAllIfEmpty $false
        if (-not $targets -or $targets.Count -eq 0) {
            throw "For action 'start', pass profile names. Example: .\\botctl.ps1 start default turbo_service"
        }
        foreach ($profile in $targets) {
            Start-Bot $profile
        }
    }

    "start-all" {
        foreach ($profile in $allProfiles) {
            Start-Bot $profile
        }
    }

    "stop" {
        $targets = Resolve-TargetProfiles -Requested $Profiles -UseAllIfEmpty $false
        if (-not $targets -or $targets.Count -eq 0) {
            throw "For action 'stop', pass profile names. Example: .\\botctl.ps1 stop default"
        }
        foreach ($profile in $targets) {
            Stop-Bot $profile
        }
    }

    "stop-all" {
        foreach ($profile in $allProfiles) {
            Stop-Bot $profile
        }
    }

    "status" {
        Print-Status -AllProfiles $allProfiles
    }
}
