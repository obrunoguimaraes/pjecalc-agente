@echo off
setlocal
cd /d %~dp0

if not exist .venv\Scripts\python.exe (
  echo Ambiente local ainda nao configurado.
  echo Execute primeiro:
  echo   powershell -ExecutionPolicy Bypass -File scripts\setup_executor_windows.ps1
  exit /b 1
)

.venv\Scripts\python.exe scripts\probe_pjecalc.py
