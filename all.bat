@echo off
cd /d "%~dp0"
start "Backend" cmd /c "start_backend.bat"
timeout /t 3 /nobreak >nul
start "Frontend" cmd /c "start_frontend.bat"