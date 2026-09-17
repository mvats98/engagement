@echo off
set "COMMENT_LOG_DIR=%~dp0appium_comments_project"
start "Comment activity" powershell.exe -NoProfile -Command "Get-Content -LiteralPath (Join-Path $env:COMMENT_LOG_DIR 'runner-local.log') -Tail 40 -Wait"
start "Comment errors" powershell.exe -NoProfile -Command "Get-Content -LiteralPath (Join-Path $env:COMMENT_LOG_DIR 'runner-local-error.log') -Tail 20 -Wait"
