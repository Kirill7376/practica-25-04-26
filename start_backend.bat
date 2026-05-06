@echo off
cd /d "%~dp0backend"
call venv\Scripts\activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
pause
