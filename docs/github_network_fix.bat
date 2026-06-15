@echo off
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting admin privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
powershell -ExecutionPolicy Bypass -File "%~dp0github_network_fix.ps1"