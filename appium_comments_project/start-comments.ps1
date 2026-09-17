$ErrorActionPreference = 'Stop'
$mutex = New-Object System.Threading.Mutex($false, 'Local\AppiumCommentsOneClick')
$locked = $false
function Test-AppiumReady {
    try {
        $status = Invoke-RestMethod 'http://127.0.0.1:4725/status' -TimeoutSec 3
        return ($status.value.ready -eq $true)
    } catch { return $false }
}
function Test-RunnerActive {
    $probe = New-Object System.Net.Sockets.Socket([System.Net.Sockets.AddressFamily]::InterNetwork, [System.Net.Sockets.SocketType]::Stream, [System.Net.Sockets.ProtocolType]::Tcp)
    try {
        $probe.Bind((New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Loopback, 47999)))
        return $false
    } catch [System.Net.Sockets.SocketException] { return $true }
    finally { $probe.Dispose() }
}
function Start-Helper($ScriptName, $LogName, $ExtraArgs) {
    $scriptPath = Join-Path $PSScriptRoot $ScriptName
    $arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $scriptPath + '" ' + $ExtraArgs
    return Start-Process powershell.exe -ArgumentList $arguments -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot "$LogName.log") -RedirectStandardError (Join-Path $PSScriptRoot "$LogName-error.log") -PassThru
}
try {
    $locked = $mutex.WaitOne(0)
    if (-not $locked) { throw 'Another launch is already in progress. Wait for that window to finish.' }
    & "$PSScriptRoot\run-local.ps1" check
    if (-not (Test-AppiumReady)) {
        Write-Host 'Starting Appium. First startup can take several minutes...'
        $server = Start-Helper 'start-appium-local.ps1' 'appium-local' ''
        $server.Id | Set-Content "$PSScriptRoot\appium-local.pid"
        $deadline = (Get-Date).AddMinutes(5)
        while (-not (Test-AppiumReady)) {
            if ($server.HasExited) { throw 'Appium stopped. See appium-local-error.log.' }
            if ((Get-Date) -gt $deadline) { throw 'Appium is still starting. See appium-local.log before trying again.' }
            Start-Sleep -Seconds 2
        }
    }
    Write-Host 'Appium is ready.'
    if (Test-RunnerActive) {
        Write-Host 'The runner is already active (port 47999 is reserved). No second copy was started.'
    } else {
        $runner = Start-Helper 'run-local.ps1' 'runner-local' 'run'
        $runner.Id | Set-Content "$PSScriptRoot\runner-local.pid"
        $deadline = (Get-Date).AddMinutes(1)
        while (-not (Test-RunnerActive)) {
            if ($runner.HasExited) { throw 'The runner stopped. See runner-local-error.log.' }
            if ((Get-Date) -gt $deadline) { throw 'Runner startup is taking longer than expected. See runner-local-error.log.' }
            Start-Sleep -Seconds 1
        }
        Write-Host 'Comment workers started in the background.'
    }
    & "$PSScriptRoot\run-local.ps1" status
    Write-Host ''
    Write-Host 'You can close this window. The workers will keep running.'
    Write-Host 'To import newly saved comments, double-click IMPORT-COMMENTS.bat.'
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
