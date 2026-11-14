[CmdletBinding()]
param(
    [switch]$AcceptExternalLicenses,
    [string]$ModelCache,
    [string]$Workspace,
    [string]$PythonExe,
    [switch]$VerifyOnly
)
$ErrorActionPreference = 'Stop'
if ($VerifyOnly) { & "$PSScriptRoot/setup.ps1" -VerifyOnly; return }
if (-not $AcceptExternalLicenses) { throw 'Read docs/LICENSE_AUDIT.md, then explicitly pass -AcceptExternalLicenses.' }
$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) { throw 'Install uv before running the complete installer; see README.md.' }
if (-not $PythonExe) {
    & $uv.Source python install 3.11.18
    if ($LASTEXITCODE -ne 0) { throw 'Pinned CPython 3.11.18 installation failed.' }
    $PythonExe = (& $uv.Source python find 3.11.18 | Select-Object -Last 1).Trim()
}
$selectedVersion = (& $PythonExe -I -c 'import sys;print(".".join(map(str,sys.version_info[:3])))' | Select-Object -Last 1).Trim()
if ($LASTEXITCODE -ne 0 -or $selectedVersion -ne '3.11.18') { throw 'Complete Classic requires CPython 3.11.18 for its frozen runtime profile.' }
$argsForBase = @{ AcceptExternalLicenses = $true; Models = 'conversion' }
if ($ModelCache) { $argsForBase.ModelCache = $ModelCache }
if ($Workspace) { $argsForBase.Workspace = $Workspace }
if ($PythonExe) { $argsForBase.PythonExe = $PythonExe }
& "$PSScriptRoot/setup.ps1" @argsForBase
if ($LASTEXITCODE -ne 0) { throw 'Conversion installation failed; screening was not started.' }
$activation = Get-Content -LiteralPath "$PSScriptRoot/.local/runtime-selection.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$screenArgs = @("$PSScriptRoot/scripts/provision_classic_screening.py", '--accept-external-licenses')
if ($ModelCache) { $screenArgs += @('--model-cache', $ModelCache) }
& $activation.python -I -X utf8 @screenArgs
if ($LASTEXITCODE -ne 0) { throw 'Screening installation incomplete; do not treat this as a complete installation.' }
Write-Host 'Complete Classic conversion and image screening stack installed. Content review remains a separate step.'
