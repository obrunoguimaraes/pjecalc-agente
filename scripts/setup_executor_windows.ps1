$ErrorActionPreference = "Stop"

Write-Host "=== AG PJe-Calc Executor - Setup Windows ==="

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Host "Python Launcher (py) nao encontrado."
    Write-Host "Instale Python 3.11 ou 3.12 e marque 'Add Python to PATH'."
    exit 1
}

if (-not (Test-Path ".venv")) {
    py -3 -m venv .venv
}

& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements-executor.txt

Write-Host "Instalando Firefox controlado pelo Playwright..."
python -m playwright install firefox

Write-Host ""
Write-Host "Setup concluido."
Write-Host "Agora execute:"
Write-Host "  python scripts\probe_pjecalc.py"
Write-Host ""
Write-Host "Se aparecer PROBE_OK, o ambiente esta pronto para o primeiro calculo."
