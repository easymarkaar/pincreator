@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo PinCreator - installation
echo ========================================

where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_COMMAND=py -3"
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python was not found.
        echo Install Python 3.11 or newer from https://www.python.org/downloads/
        echo During installation, enable "Add Python to PATH".
        pause
        exit /b 1
    )
    set "PYTHON_COMMAND=python"
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PYTHON_COMMAND% -m venv .venv
    if errorlevel 1 goto :error
) else (
    echo Virtual environment already exists.
)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo [OK] Installation completed.
echo Double-click run.bat to start PinCreator.
pause
exit /b 0

:error
echo.
echo [ERROR] Installation failed. Review the messages above.
pause
exit /b 1

