Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path .\.venv\Scripts\Activate.ps1)) {
    Write-Error "Virtual environment not found. Create it first with: python -m venv .venv"
}

. .\.venv\Scripts\Activate.ps1
python tests\smoke_test.py
