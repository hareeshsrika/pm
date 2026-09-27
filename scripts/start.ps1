$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    docker compose up -d --build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Output "Project Management MVP is available at http://localhost:8000"
}
finally {
    Pop-Location
}
