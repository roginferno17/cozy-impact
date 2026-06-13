@echo off
REM ============================================================
REM  flik - run for real (presses F during dialogue).
REM  Self-elevates to Administrator so keypresses reach Genshin,
REM  which itself runs as Administrator.
REM ============================================================

REM --- are we admin already? if not, relaunch elevated ---
net session >nul 2>&1
if %errorlevel% neq 0 (
  powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

cd /d "%~dp0"
echo Starting flik... (F9 = pause/resume, F12 = quit)
echo.
python run.py
echo.
pause
