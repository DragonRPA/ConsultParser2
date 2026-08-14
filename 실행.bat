@echo off
cd /d "%~dp0"
"C:\ProgramData\anaconda3\python.exe" main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Application crashed or finished with error.
    pause
)
