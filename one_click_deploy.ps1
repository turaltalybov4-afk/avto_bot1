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

$bootstrapFlag = if ($SkipBootstrap) { "0" } else { "1" }

$remoteScript = @"
set -e

REPO_DIR='$(ConvertTo-SingleQuoteEscaped $RepoDir)'
SERVICE_NAME='$(ConvertTo-SingleQuoteEscaped $ServiceName)'
BOT_USER='$(ConvertTo-SingleQuoteEscaped $BotUser)'
DATA_DIR='$(ConvertTo-SingleQuoteEscaped $DataDir)'
ENV_FILE='$(ConvertTo-SingleQuoteEscaped $EnvFile)'
PROFILE='$(ConvertTo-SingleQuoteEscaped $ClientKey)'
BOT_TOKEN='$(ConvertTo-SingleQuoteEscaped $BotToken)'
MANAGERS='$(ConvertTo-SingleQuoteEscaped $ManagerIds)'
DB_FILE='$(ConvertTo-SingleQuoteEscaped $dbFile)'
REPO_URL='$(ConvertTo-SingleQuoteEscaped $repoUrlValue)'
BRANCH='$(ConvertTo-SingleQuoteEscaped $Branch)'
DO_BOOTSTRAP='$(ConvertTo-SingleQuoteEscaped $bootstrapFlag)'

if [ ! -d "/tmp/setup_repo/.git" ]; then
    git clone "\$REPO_URL" /tmp/setup_repo
else
    git -C /tmp/setup_repo pull origin "\$BRANCH"
fi

if [ "\$DO_BOOTSTRAP" = "1" ]; then
    if [ ! -f "/etc/systemd/system/\$SERVICE_NAME.service" ]; then
        printf "%s\n" "\$REPO_URL" | BOT_USER="\$BOT_USER" BOT_DIR="\$REPO_DIR" BOT_DATA_DIR="\$DATA_DIR" BOT_ENV_FILE="\$ENV_FILE" SERVICE_NAME="\$SERVICE_NAME" bash /tmp/setup_repo/deploy/setup.sh
    fi
fi

if [ ! -d "\$REPO_DIR/.git" ]; then
  git clone "\$REPO_URL" "\$REPO_DIR"
fi

cd "\$REPO_DIR"
git pull origin "\$BRANCH"

mkdir -p "\$DATA_DIR"
chown -R "\$BOT_USER":"\$BOT_USER" "\$DATA_DIR"
chmod 750 "\$DATA_DIR"

cat > "\$ENV_FILE" <<EOF
BOT_TOKEN=\$BOT_TOKEN
AUTOBOT_PROFILE=\$PROFILE
AUTOBOT_MANAGERS=\$MANAGERS
AUTOBOT_DATABASE_FILE=\$DB_FILE
EOF

chmod 600 "\$ENV_FILE"
systemctl daemon-reload
systemctl enable "\$SERVICE_NAME"
systemctl restart "\$SERVICE_NAME"

echo "--- RESULT ---"
systemctl is-enabled "\$SERVICE_NAME"
systemctl is-active "\$SERVICE_NAME"
systemctl status "\$SERVICE_NAME" --no-pager
journalctl -u "\$SERVICE_NAME" -n 30 --no-pager
"@

Write-Host "[2/4] Deploy to VPS..." -ForegroundColor Green
$target = "$SshUser@$ServerIp"
$remoteScript = $remoteScript -replace "`r", ""
$remoteScript | ssh $target "bash -se"
if ($LASTEXITCODE -ne 0) {
    throw "Remote deploy failed with exit code $LASTEXITCODE"
}

Write-Host "[3/4] Done." -ForegroundColor Green
Write-Host "[4/4] If Telegram still does not respond, test /start and share last 20 log lines." -ForegroundColor Yellow
