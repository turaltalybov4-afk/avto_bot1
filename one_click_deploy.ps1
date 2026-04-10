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
    [switch]$SkipBootstrap,
    [switch]$ReuseSshSession,
    [string]$SshControlPath = "~/.ssh/autobot-%r@%h:%p",
    [int]$SshControlPersistMinutes = 30
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
$sshArgs = @()
if ($ReuseSshSession) {
    $persistMinutes = [Math]::Max($SshControlPersistMinutes, 1)
    $sshArgs += @(
        "-o", "ControlMaster=auto",
        "-o", "ControlPersist=${persistMinutes}m",
        "-o", "ControlPath=$SshControlPath"
    )
}

function Invoke-RemoteDeploy([string[]]$ExtraSshArgs) {
    $remoteScript | ssh @ExtraSshArgs $target "bash -se"
    return $LASTEXITCODE
}

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
$rSkipBootstrap = if ($SkipBootstrap) { "1" } else { "0" }

$remoteScript = @"
set -e

REPO_DIR='$rRepoDir'
SERVICE_NAME='$rServiceName'
BOT_USER='$rBotUser'
DATA_DIR='$rDataDir'
ENV_FILE='$rEnvFile'
PROFILE='$rClientKey'
BOT_TOKEN='$rBotToken'
MANAGERS='$rManagerIds'
DB_FILE='$rDbFile'
REPO_URL='$rRepoUrl'
BRANCH='$rBranch'
SKIP_BOOTSTRAP='$rSkipBootstrap'

if [ -d /tmp/setup_repo/.git ]; then
    if [ -n "`$(git -C /tmp/setup_repo status --porcelain)" ]; then
        git -C /tmp/setup_repo stash push -u -m "autodeploy-setup-repo-`$(date +%Y%m%d-%H%M%S)" || true
    fi
    git -C /tmp/setup_repo pull origin "`$BRANCH"
else
    git clone "`$REPO_URL" /tmp/setup_repo
fi

[ "`$SKIP_BOOTSTRAP" = "1" ] || [ -f "/etc/systemd/system/`$SERVICE_NAME.service" ] || {
    id "`$BOT_USER" > /dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin "`$BOT_USER"
    mkdir -p "`$REPO_DIR" "`$DATA_DIR"
    cp /tmp/setup_repo/deploy/autobot.service "/etc/systemd/system/`$SERVICE_NAME.service"
    sed -i "s|SETUP_BOT_DIR|`$REPO_DIR|g" "/etc/systemd/system/`$SERVICE_NAME.service"
    sed -i "s|SETUP_BOT_USER|`$BOT_USER|g" "/etc/systemd/system/`$SERVICE_NAME.service"
    sed -i "s|SETUP_BOT_ENV_FILE|`$ENV_FILE|g" "/etc/systemd/system/`$SERVICE_NAME.service"
    systemctl daemon-reload
}

if [ -d "`$REPO_DIR/.git" ]; then
    if [ -n "`$(git -C "`$REPO_DIR" status --porcelain)" ]; then
        git -C "`$REPO_DIR" stash push -u -m "autodeploy-target-repo-`$(date +%Y%m%d-%H%M%S)" || true
    fi
else
    git clone "`$REPO_URL" "`$REPO_DIR"
fi
cd "`$REPO_DIR"
git pull origin "`$BRANCH"

if [ ! -x "`$REPO_DIR/.venv/bin/python" ]; then
    python3 -m venv "`$REPO_DIR/.venv"
    "`$REPO_DIR/.venv/bin/pip" install --upgrade pip setuptools wheel
    "`$REPO_DIR/.venv/bin/pip" install -r "`$REPO_DIR/requirements.txt"
fi

mkdir -p "`$DATA_DIR"
chown -R "`$BOT_USER":"`$BOT_USER" "`$DATA_DIR"
chmod 750 "`$DATA_DIR"

cat > "`$ENV_FILE" <<EOF
BOT_TOKEN=`$BOT_TOKEN
AUTOBOT_PROFILE=`$PROFILE
AUTOBOT_MANAGERS=`$MANAGERS
AUTOBOT_DATABASE_FILE=`$DB_FILE
EOF

chmod 600 "`$ENV_FILE"
systemctl daemon-reload
systemctl enable "`$SERVICE_NAME"
systemctl kill --signal=SIGKILL "`$SERVICE_NAME" 2>/dev/null || true
systemctl reset-failed "`$SERVICE_NAME" || true
systemctl restart "`$SERVICE_NAME"

systemctl is-enabled "`$SERVICE_NAME" >/dev/null

# Give systemd a short window to bring the service up before deciding it's failed.
ATTEMPTS=30
SLEEP_SEC=1
STATE="unknown"
for i in `$(seq 1 "`$ATTEMPTS"); do
    STATE="`$(systemctl is-active "`$SERVICE_NAME" || true)"
    if [ "`$STATE" = "active" ]; then
        break
    fi
    if [ "`$STATE" = "failed" ]; then
        break
    fi
    sleep "`$SLEEP_SEC"
done

if [ "`$STATE" != "active" ]; then
    echo "ERROR: service '`$SERVICE_NAME' is '`$STATE' after restart"
    echo "--- systemctl status (tail) ---"
    systemctl status "`$SERVICE_NAME" --no-pager | tail -n 30 || true
    echo "--- journal (last 40 lines, recent) ---"
    journalctl -u "`$SERVICE_NAME" -n 40 --since "-10 min" --no-pager || true
    exit 1
fi

echo "Service '`$SERVICE_NAME' is active"
"@

$remoteScript = $remoteScript -replace "`r", ""
$exitCode = Invoke-RemoteDeploy -ExtraSshArgs $sshArgs
if ($exitCode -ne 0 -and $ReuseSshSession) {
    Write-Host "SSH session reuse failed, retrying without multiplexing..." -ForegroundColor Yellow
    $exitCode = Invoke-RemoteDeploy -ExtraSshArgs @()
}

if ($exitCode -ne 0) {
    throw "Remote deploy failed with exit code $exitCode"
}

Write-Host "[3/4] Done." -ForegroundColor Green
Write-Host "[4/4] If Telegram still does not respond, test /start and share last 20 log lines." -ForegroundColor Yellow
