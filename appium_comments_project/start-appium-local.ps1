$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\environment.ps1"
$appium = Get-Command appium.cmd -ErrorAction SilentlyContinue
if (-not $appium) { $appium = Get-Command appium -ErrorAction SilentlyContinue }
if (-not $appium) { throw 'Appium is missing. Install it with npm install -g appium and add it to PATH.' }
& $appium.Source --address 127.0.0.1 --port 4725
exit $LASTEXITCODE
