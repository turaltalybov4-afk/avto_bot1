param(
    [string]$ServerIp = "146.103.42.126",
    [string]$ManagerIds = "8673882143",
    [string]$ClientProfile = "turbo_service",
    [string]$RepoUrl = "https://github.com/turaltalybov4-afk/avto_bot1.git"
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$token = Read-Host "Paste TOKEN for autobot2"
if ([string]::IsNullOrWhiteSpace($token)) {
    throw "Token is required"
}

powershell -ExecutionPolicy Bypass -File ".\one_click_deploy.ps1" `
    -ServerIp $ServerIp `
    -ServiceName "autobot2" `
    -BotUser "botuser2" `
    -RepoDir "/opt/auto_bot2" `
    -DataDir "/var/lib/auto_bot2" `
    -EnvFile "/etc/auto_bot2.env" `
    -BotToken $token `
    -ManagerIds $ManagerIds `
    -ClientProfile $ClientProfile `
    -RepoUrl $RepoUrl
