@echo off
cd /d "%~dp0"
python setup.py
if errorlevel 1 echo Setup failed. Install Python 3.10+ and add it to PATH, then retry.
pause
