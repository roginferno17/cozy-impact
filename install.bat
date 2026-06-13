@echo off
REM ============================================================
REM  flik - one-time setup. Double-click this FIRST.
REM  Installs the Python libraries flik needs.
REM ============================================================
cd /d "%~dp0"
echo Installing flik's requirements...
echo.
python -m pip install -r requirements.txt
echo.
if %errorlevel% neq 0 (
  echo.
  echo  Something went wrong. Make sure Python is installed and that
  echo  "python" works in this window, then run this file again.
) else (
  echo  All set!  You can now double-click  observe.bat  to test safely,
  echo  or  flik.bat  to run it for real.
)
echo.
pause
