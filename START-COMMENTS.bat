@echo off
title Comment Runner
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0appium_comments_project\start-comments.ps1"
echo.
pause
