@echo off
title Stop Comments
set "COMMENT_STOP_FILE=%~dp0appium_comments_project\comments.stop"
powershell.exe -NoProfile -Command "$ErrorActionPreference = 'Stop'; [System.IO.File]::WriteAllText($env:COMMENT_STOP_FILE, 'stop')"
if errorlevel 1 (
    echo Failed to request stop.
) else (
    echo Stop requested. Current comments and cleanup will finish before workers exit.
    echo VIEW-LOGS.bat shows when the comment workers have stopped.
    echo After they stop, use START-COMMENTS.bat to start again.
)
pause
