[CmdletBinding()]
param(
    [string]$CsvPath = (Join-Path $PSScriptRoot 'cameras.csv'),
    [string]$TemplatePath = (Join-Path $PSScriptRoot 'comparison_template.html'),
    [string]$OutputDir = (Join-Path $PSScriptRoot 'guides')
)

$ErrorActionPreference = 'Stop'
$generator = Join-Path $PSScriptRoot 'tools/generate_comparisons.py'
$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3 is required to generate comparison pages.' }

& $python.Source $generator --csv $CsvPath --template $TemplatePath --output-dir $OutputDir
if ($LASTEXITCODE -ne 0) { throw "Comparison generator failed with exit code $LASTEXITCODE" }
