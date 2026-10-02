Set-Location -LiteralPath $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $taskPython)) {
    python -m venv .venv
    & $taskPython -m pip install -r requirements.txt
}
if (!(Test-Path -LiteralPath '.env')) { Copy-Item -LiteralPath '.env.example' -Destination '.env' }
& $taskPython -m backend.seed
& $taskPython -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
