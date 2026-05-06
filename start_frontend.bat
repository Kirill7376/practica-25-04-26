@echo off
cd /d "%~dp0chat_app"
flutter run -d web-server --web-port=8080
pause