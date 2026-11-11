<#
.SYNOPSIS
    Label-Forge Phase 1.1 Automated Evidence Validation Suite (PowerShell Wrapper)
.DESCRIPTION
    Executes scripts/validate-phase1-evidence.py and returns deterministic exit codes:
      0: PASS
      1: FAIL
      2: PREREQUISITE_ERROR
#>

[CmdletBinding()]
param()

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir "validate-phase1-evidence.py"

if (-not (Test-Path $PythonScript)) {
    Write-Error "Validation script not found: $PythonScript"
    exit 2
}

& python $PythonScript
$ExitCode = $LASTEXITCODE

exit $ExitCode
