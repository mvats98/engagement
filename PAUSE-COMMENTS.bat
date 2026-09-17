@echo off
title Pause Comments
set "COMMENT_PAUSE_FILE=%~dp0appium_comments_project\comments.paused"
powershell.exe -NoProfile -Command "$ErrorActionPreference = 'Stop'; [System.IO.File]::WriteAllText($env:COMMENT_PAUSE_FILE, 'paused')"
if errorlevel 1 (
    echo Failed to request pause.
) else (
    echo Pause requested. Any in-progress comment will finish first.
    echo Use RESUME-COMMENTS.bat to continue.
)
pause
