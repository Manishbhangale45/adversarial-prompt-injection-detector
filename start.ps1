Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force

$workspaceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Join-Path $workspaceRoot "project"
$venvActivate = Join-Path $workspaceRoot ".venv\Scripts\Activate.ps1"
$modelPath = Join-Path $projectPath "models\prompt_detector.pkl"

if (-not (Test-Path $venvActivate)) {
    Write-Error "Virtual environment not found at $venvActivate"
    exit 1
}

Push-Location $projectPath
try {
    & $venvActivate

    if (-not (Test-Path $modelPath)) {
        Write-Host "Training model because prompt_detector.pkl is missing..."
        python train_model.py
        if ($LASTEXITCODE -ne 0) {
            throw "Model training failed."
        }
    }

    python app.py
}
finally {
    Pop-Location
}