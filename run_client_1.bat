@echo off
cd /d "%~dp0"
set "AUTOBOT_PROFILE=Клиент 1"
.\.venv\Scripts\python.exe .\main.py
pause
