param(
    [string]$ServerIp = "146.103.42.126",
    [string]$RepoUrl = "https://github.com/turaltalybov4-afk/avto_bot1.git",
    [string]$Branch = "main",
    [string]$DefaultManagerIds = "6271000700"
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "=== Universal one-click deploy ===" -ForegroundColor Cyan
Write-Host "This script deploys bot #1, #2, #3 ... on one VPS." -ForegroundColor DarkCyan

$botNumberRaw = Read-Host "Bot number (1 for autobot, 2 for autobot2, 3 for autobot3, ...)"
if ([string]::IsNullOrWhiteSpace($botNumberRaw)) {
    throw "Bot number is required"
}

[int]$botNumber = 0
if (-not [int]::TryParse($botNumberRaw, [ref]$botNumber) -or $botNumber -lt 1) {
    throw "Bot number must be an integer >= 1"
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

if ($botNumber -eq 1) {
    $serviceName = "autobot"
    $botUser = "botuser"
    $repoDir = "/opt/auto_bot"
    $dataDir = "/var/lib/auto_bot"
    $envFile = "/etc/auto_bot.env"
}
else {
    $serviceName = "autobot$botNumber"
    $botUser = "botuser$botNumber"
    $repoDir = "/opt/auto_bot$botNumber"
    $dataDir = "/var/lib/auto_bot$botNumber"
    $envFile = "/etc/auto_bot$botNumber.env"
}

Write-Host "" 
Write-Host "Deploy summary:" -ForegroundColor Green
Write-Host "Server:      $ServerIp"
Write-Host "Service:     $serviceName"
Write-Host "Profile:     $clientKey"
Write-Host "Managers:    $managerIds"
Write-Host "RepoDir:     $repoDir"
Write-Host "DataDir:     $dataDir"
Write-Host "EnvFile:     $envFile"
Write-Host "" 

$confirm = Read-Host "Type YES to deploy"
if ($confirm -ne "YES") {
    throw "Deployment canceled"
}

powershell -ExecutionPolicy Bypass -File ".\one_click_deploy.ps1" `
    -ServerIp $ServerIp `
    -ServiceName $serviceName `
    -BotUser $botUser `
    -RepoDir $repoDir `
    -DataDir $dataDir `
    -EnvFile $envFile `
    -BotToken $token `
    -ManagerIds $managerIds `
    -ClientKey $clientKey `
    -RepoUrl $RepoUrl `
    -Branch $Branch

Write-Host "" 
Write-Host "Done. Quick check:" -ForegroundColor Green
Write-Host "ssh root@$ServerIp \"systemctl is-active $serviceName; systemctl is-enabled $serviceName; systemctl status $serviceName --no-pager\""
