param(
    [Parameter(Mandatory = $true)]
    [string]$ServerIp,

    [Parameter(Mandatory = $true)]
    [string]$BotToken,

    [Parameter(Mandatory = $true)]
    [string]$ManagerIds,

    [string]$ClientKey = "default",
    [string]$SshUser = "root",
    [string]$RepoDir = "/opt/auto_bot",
    [string]$ServiceName = "autobot",
    [string]$BotUser = "botuser",
    [string]$DataDir = "/var/lib/auto_bot",
    [string]$EnvFile = "/etc/auto_bot.env",
    [string]$RepoUrl = "",
    [string]$Branch = "main",
    [switch]$SkipBootstrap
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function ConvertTo-SingleQuoteEscaped([string]$v) {
    return $v.Replace("'", "'\''")
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is not installed or not found in PATH"
}

Write-Host "[1/4] Push local changes to GitHub..." -ForegroundColor Green
& git add -A
& git commit -m "auto deploy $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "No new commit created (nothing to commit or commit already exists)." -ForegroundColor Yellow
}
& git push origin $Branch
if ($LASTEXITCODE -ne 0) {
    throw "git push failed with exit code $LASTEXITCODE"
}

$dbFile = "{0}/auto_{1}.db" -f $DataDir.TrimEnd('/'), $ClientKey
$repoUrlValue = if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
        & git config --get remote.origin.url
} else {
        $RepoUrl
}

if ([string]::IsNullOrWhiteSpace($repoUrlValue)) {
        throw "RepoUrl is empty and remote.origin.url was not found. Pass -RepoUrl explicitly."
}

Write-Host "[2/4] Deploy to VPS..." -ForegroundColor Green
$target = "$SshUser@$ServerIp"

$rRepoDir = ConvertTo-SingleQuoteEscaped $RepoDir
$rServiceName = ConvertTo-SingleQuoteEscaped $ServiceName
$rBotUser = ConvertTo-SingleQuoteEscaped $BotUser
$rDataDir = ConvertTo-SingleQuoteEscaped $DataDir
$rEnvFile = ConvertTo-SingleQuoteEscaped $EnvFile
$rClientKey = ConvertTo-SingleQuoteEscaped $ClientKey
$rBotToken = ConvertTo-SingleQuoteEscaped $BotToken
$rManagerIds = ConvertTo-SingleQuoteEscaped $ManagerIds
$rDbFile = ConvertTo-SingleQuoteEscaped $dbFile
$rRepoUrl = ConvertTo-SingleQuoteEscaped $repoUrlValue
$rBranch = ConvertTo-SingleQuoteEscaped $Branch

function Invoke-RemoteStrict([string]$cmd) {
    & ssh $target $cmd
    if ($LASTEXITCODE -ne 0) {
        throw "Remote deploy failed with exit code $LASTEXITCODE"
    }
}

Invoke-RemoteStrict "[ -d /tmp/setup_repo/.git ] && git -C /tmp/setup_repo pull origin '$rBranch' || git clone '$rRepoUrl' /tmp/setup_repo"

$serviceExistsCmd = "test -f '/etc/systemd/system/$rServiceName.service'"
& ssh $target $serviceExistsCmd
$serviceExists = ($LASTEXITCODE -eq 0)

if (-not $SkipBootstrap -and -not $serviceExists) {
    Invoke-RemoteStrict "printf '%s\n' '$rRepoUrl' | BOT_USER='$rBotUser' BOT_DIR='$rRepoDir' BOT_DATA_DIR='$rDataDir' BOT_ENV_FILE='$rEnvFile' SERVICE_NAME='$rServiceName' bash /tmp/setup_repo/deploy/setup.sh"
}

Invoke-RemoteStrict "[ -d '$rRepoDir/.git' ] || git clone '$rRepoUrl' '$rRepoDir'"
Invoke-RemoteStrict "cd '$rRepoDir' && git pull origin '$rBranch'"
Invoke-RemoteStrict "mkdir -p '$rDataDir' && chown -R '$rBotUser':'$rBotUser' '$rDataDir' && chmod 750 '$rDataDir'"
Invoke-RemoteStrict "printf '%s\n' 'BOT_TOKEN=$rBotToken' 'AUTOBOT_PROFILE=$rClientKey' 'AUTOBOT_MANAGERS=$rManagerIds' 'AUTOBOT_DATABASE_FILE=$rDbFile' > '$rEnvFile'"
Invoke-RemoteStrict "chmod 600 '$rEnvFile' && systemctl daemon-reload && systemctl enable '$rServiceName' && systemctl restart '$rServiceName'"

& ssh $target "systemctl is-enabled '$rServiceName'; systemctl is-active '$rServiceName'; systemctl status '$rServiceName' --no-pager; journalctl -u '$rServiceName' -n 30 --no-pager"
if ($LASTEXITCODE -ne 0) {
    throw "Remote status check failed with exit code $LASTEXITCODE"
}

Write-Host "[3/4] Done." -ForegroundColor Green
Write-Host "[4/4] If Telegram still does not respond, test /start and share last 20 log lines." -ForegroundColor Yellow
