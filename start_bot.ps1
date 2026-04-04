param(
    [Parameter(Mandatory = $true)]
    [string]$Profile
)

Set-Location -Path $PSScriptRoot
$env:AUTOBOT_PROFILE = $Profile
& ".\.venv\Scripts\python.exe" ".\main.py"
