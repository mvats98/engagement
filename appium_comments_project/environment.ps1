# Preserve shell overrides; fall back to persisted settings when needed.
foreach ($variable in @('ANDROID_HOME', 'JAVA_HOME')) {
    if (-not [Environment]::GetEnvironmentVariable($variable, 'Process')) {
        $value = [Environment]::GetEnvironmentVariable($variable, 'User')
        if (-not $value) { $value = [Environment]::GetEnvironmentVariable($variable, 'Machine') }
        if ($value) { [Environment]::SetEnvironmentVariable($variable, $value, 'Process') }
    }
}
if (-not $env:ANDROID_HOME -and $env:ANDROID_SDK_ROOT) { $env:ANDROID_HOME = $env:ANDROID_SDK_ROOT }
if ($env:ANDROID_HOME) { $env:Path += ";$env:ANDROID_HOME\platform-tools;$env:ANDROID_HOME\cmdline-tools\latest\bin" }
if ($env:JAVA_HOME) { $env:Path += ";$env:JAVA_HOME\bin" }
if ($env:APPDATA) { $env:Path += ";$env:APPDATA\npm" }
$env:PYTHONUTF8 = '1'
$env:PYTHONUNBUFFERED = '1'
