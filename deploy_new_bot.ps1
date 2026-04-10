param(
    [string]$ServerIp = "146.103.42.126",
    [string]$RepoUrl = "https://github.com/turaltalybov4-afk/avto_bot1.git",
    [string]$Branch = "main",
    [string]$DefaultManagerIds = "6271000700",
    [int]$BotNumber = 0,
    [switch]$DeployAll,
    [switch]$UseSavedConfig,
    [switch]$Yes,
    [string]$ConfigFile = "deploy_bots.json",
    [switch]$NoSshSessionReuse
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
$enableSshSessionReuse = -not $NoSshSessionReuse
$sshControlPath = "~/.ssh/autobot-$($ServerIp)-%r@%h:%p"

function Get-DeployTarget([int]$Number) {
    if ($Number -lt 1) {
        throw "Bot number must be an integer >= 1"
    }

    if ($Number -eq 1) {
        return @{
            ServiceName = "autobot"
            BotUser     = "botuser"
            RepoDir     = "/opt/auto_bot"
            DataDir     = "/var/lib/auto_bot"
            EnvFile     = "/etc/auto_bot.env"
        }
    }

    return @{
        ServiceName = "autobot$Number"
        BotUser     = "botuser$Number"
        RepoDir     = "/opt/auto_bot$Number"
        DataDir     = "/var/lib/auto_bot$Number"
        EnvFile     = "/etc/auto_bot$Number.env"
    }
}

function Load-SavedConfig([string]$Path) {
    if (-not (Test-Path $Path)) {
        $fallbackPath = "deploy_bots.example.json"
        if ($Path -eq "deploy_bots.json" -and (Test-Path $fallbackPath)) {
            Write-Host "Config file not found: $Path" -ForegroundColor Yellow
            Write-Host "Using fallback config: $fallbackPath" -ForegroundColor Yellow
            $Path = $fallbackPath
        }
        else {
            throw "Config file not found: $Path"
        }
    }
    $raw = Get-Content -Path $Path -Raw
    if ([string]::IsNullOrWhiteSpace($raw)) {
        throw "Config file is empty: $Path"
    }
    return $raw | ConvertFrom-Json
}

function Resolve-ManagerIds([string]$Value, [string]$Fallback) {
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $Fallback
    }
    return $Value
}

function Invoke-Deploy([int]$Number, [string]$Profile, [string]$Token, [string]$ManagerIds) {
    if ([string]::IsNullOrWhiteSpace($Profile)) {
        throw "Profile key is required for bot #$Number"
    }
    if ([string]::IsNullOrWhiteSpace($Token)) {
        throw "Bot token is required for bot #$Number"
    }

    $target = Get-DeployTarget $Number

    Write-Host ""
    Write-Host "Deploy summary:" -ForegroundColor Green
    Write-Host "Server:      $ServerIp"
    Write-Host "Service:     $($target.ServiceName)"
    Write-Host "Profile:     $Profile"
    Write-Host "Managers:    $ManagerIds"
    Write-Host "RepoDir:     $($target.RepoDir)"
    Write-Host "DataDir:     $($target.DataDir)"
    Write-Host "EnvFile:     $($target.EnvFile)"
    Write-Host ""

    $deployArgs = @(
        "-ExecutionPolicy", "Bypass",
        "-File", ".\\one_click_deploy.ps1",
        "-ServerIp", $ServerIp,
        "-ServiceName", $target.ServiceName,
        "-BotUser", $target.BotUser,
        "-RepoDir", $target.RepoDir,
        "-DataDir", $target.DataDir,
        "-EnvFile", $target.EnvFile,
        "-BotToken", $Token,
        "-ManagerIds", $ManagerIds,
        "-ClientKey", $Profile,
        "-RepoUrl", $RepoUrl,
        "-Branch", $Branch,
        "-SshControlPath", $sshControlPath
    )

    if ($enableSshSessionReuse) {
        $deployArgs += "-ReuseSshSession"
    }

    & powershell @deployArgs

    Write-Host ""
    Write-Host "Done. Quick check:" -ForegroundColor Green
    Write-Host ('ssh root@{0} "systemctl is-active {1}; systemctl is-enabled {1}; systemctl status {1} --no-pager"' -f $ServerIp, $target.ServiceName)
}

Write-Host "=== Universal one-click deploy ===" -ForegroundColor Cyan
Write-Host "This script deploys bot #1, #2, #3 ... on one VPS." -ForegroundColor DarkCyan

if ($DeployAll -and -not $UseSavedConfig) {
    throw "-DeployAll requires -UseSavedConfig"
}

if ($DeployAll) {
    $cfg = Load-SavedConfig $ConfigFile
    $savedDefaultManagers = Resolve-ManagerIds -Value $cfg.defaultManagerIds -Fallback $DefaultManagerIds
    $bots = @($cfg.bots)
    if (-not $bots -or $bots.Count -eq 0) {
        throw "No bots found in config file: $ConfigFile"
    }

    if (-not $Yes) {
        $confirmAll = Read-Host "Type YES to deploy ALL bots from $ConfigFile"
        if ($confirmAll -ne "YES") {
            throw "Deployment canceled"
        }
    }

    foreach ($bot in ($bots | Sort-Object number)) {
        [int]$number = [int]$bot.number
        $profile = [string]$bot.profile
        $token = [string]$bot.token
        $managerIds = Resolve-ManagerIds -Value ([string]$bot.managerIds) -Fallback $savedDefaultManagers
        Invoke-Deploy -Number $number -Profile $profile -Token $token -ManagerIds $managerIds
    }

    return
}

if ($UseSavedConfig -and $BotNumber -gt 0) {
    $cfg = Load-SavedConfig $ConfigFile
    $savedDefaultManagers = Resolve-ManagerIds -Value $cfg.defaultManagerIds -Fallback $DefaultManagerIds
    $bot = @($cfg.bots) | Where-Object { [int]$_.number -eq $BotNumber } | Select-Object -First 1
    if (-not $bot) {
        throw "Bot #$BotNumber not found in $ConfigFile"
    }

    if (-not $Yes) {
        $confirmSaved = Read-Host "Type YES to deploy bot #$BotNumber from $ConfigFile"
        if ($confirmSaved -ne "YES") {
            throw "Deployment canceled"
        }
    }

    Invoke-Deploy `
        -Number $BotNumber `
        -Profile ([string]$bot.profile) `
        -Token ([string]$bot.token) `
        -ManagerIds (Resolve-ManagerIds -Value ([string]$bot.managerIds) -Fallback $savedDefaultManagers)
    return
}

if ($BotNumber -le 0) {
    $botNumberRaw = Read-Host "Bot number (1 for autobot, 2 for autobot2, 3 for autobot3, ...)"
    if ([string]::IsNullOrWhiteSpace($botNumberRaw)) {
        throw "Bot number is required"
    }

    [int]$parsedNumber = 0
    if (-not [int]::TryParse($botNumberRaw, [ref]$parsedNumber) -or $parsedNumber -lt 1) {
        throw "Bot number must be an integer >= 1"
    }
    $BotNumber = $parsedNumber
}

$clientKey = Read-Host "Profile file name without .py (example: turbo_service)"
if ([string]::IsNullOrWhiteSpace($clientKey)) {
    throw "Profile key is required"
}

$managerIds = Read-Host "Manager IDs comma-separated [default: $DefaultManagerIds]"
if ([string]::IsNullOrWhiteSpace($managerIds)) {
    $managerIds = $DefaultManagerIds
}

$token = Read-Host "Paste BOT TOKEN"
if ([string]::IsNullOrWhiteSpace($token)) {
    throw "Bot token is required"
}

if (-not $Yes) {
    $confirm = Read-Host "Type YES to deploy"
    if ($confirm -ne "YES") {
        throw "Deployment canceled"
    }
}

Invoke-Deploy -Number $BotNumber -Profile $clientKey -Token $token -ManagerIds $managerIds
