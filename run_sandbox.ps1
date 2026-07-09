$ErrorActionPreference = "Stop"

$workspaceDir = "c:\Users\saipr\Capstone"
$dataDir = Join-Path $workspaceDir "data"
$scriptsDir = Join-Path $workspaceDir "scripts"
$venvDir = Join-Path $workspaceDir ".venv_sandbox"

# Ensure data/output directory exists
$outputDir = Join-Path $dataDir "output"
if (-Not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
}

Write-Host "Setting up local Python Sandbox Environment..."
if (-Not (Test-Path $venvDir)) {
    python -m venv $venvDir
}

# Activate venv and install dependencies
$pythonExe = Join-Path $venvDir "Scripts\python.exe"
$pipExe = Join-Path $venvDir "Scripts\pip.exe"

& $pipExe install -q pandas openpyxl

Write-Host "Executing Parsing Agent script inside local Sandbox..."
& $pythonExe (Join-Path $scriptsDir "extract_menu.py")

Write-Host "Execution Finished."
