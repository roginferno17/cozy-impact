@echo off
REM ============================================================
REM  flik - SAFE TEST MODE (observe only).
REM  Watches the screen and prints what it WOULD do, but never
REM  presses F. Use this first to make sure it only reacts to
REM  real dialogue. Self-elevates so the screen reads correctly.
REM ============================================================

net session >nul 2>&1
if %errorlevel% neq 0 (
  powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

cd /d "%~dp0"
echo Starting flik in SAFE TEST MODE - F will NOT be pressed.
echo Any moment flik thinks it sees dialogue, it saves a picture to the
echo  "flik-captures" folder so we can check it later.
echo (F9 = pause/resume, F12 = quit)
echo.
python run.py --dry-run --verbose --capture
echo.
pause
