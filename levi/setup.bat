@echo off
REM Quick setup script for LEVI Assistant on Windows

echo.
echo ========================================
echo LEVI Assistant - Quick Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Python found ✓
python --version

REM Create virtual environment
echo.
echo [2/4] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created ✓
) else (
    echo Virtual environment already exists ✓
)

REM Activate virtual environment
echo.
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo [4/4] Installing dependencies...
echo This may take a few minutes...
pip install -r requirements.txt --quiet

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup Complete! ✓
echo ========================================
echo.
echo To start LEVI:
echo   python main.py
echo.
pause
