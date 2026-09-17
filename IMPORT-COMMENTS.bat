@echo off
title Import Comments
echo Imports all saved comments from comment_data.txt.
echo Use only new work in an edited file; identical imports are ignored.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0appium_comments_project\run-local.ps1" enqueue
echo.
pause
