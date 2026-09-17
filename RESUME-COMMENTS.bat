@echo off
title Resume Comments
set "COMMENT_PAUSE_FILE=%~dp0appium_comments_project\comments.paused"
powershell.exe -NoProfile -Command "$ErrorActionPreference = 'Stop'; if (Test-Path -LiteralPath $env:COMMENT_PAUSE_FILE) { Remove-Item -LiteralPath $env:COMMENT_PAUSE_FILE }"
if errorlevel 1 (
    echo Failed to resume comments.
) else (
    echo Pause cleared. Running workers will continue automatically.
    echo If the runner is stopped, use START-COMMENTS.bat.
)
pause
