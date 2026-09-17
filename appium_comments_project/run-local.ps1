param(
    [ValidateSet('check', 'enqueue', 'status', 'export', 'run')]
    [string]$Command = 'status',
    [string]$Source
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\environment.ps1"
$pythonPath = Join-Path $PSScriptRoot '.venv-local\Scripts\python.exe'
if (-not (Test-Path $pythonPath)) { throw 'Run SETUP.bat from the project root to install the local Python environment.' }
Push-Location $PSScriptRoot
try {
    if ($Source) { & $pythonPath multi_device.py $Command --source $Source }
    else { & $pythonPath multi_device.py $Command }
    if ($LASTEXITCODE -ne 0) { throw "Runner exited with code $LASTEXITCODE" }
} finally { Pop-Location }
