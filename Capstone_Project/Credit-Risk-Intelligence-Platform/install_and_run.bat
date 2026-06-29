@echo off
:: ============================================================
:: Credit Risk Intelligence Platform — Windows Launcher
:: Double-click this file to install and run the application.
:: Requirements: Python 3.10, 3.11, or 3.12 installed
:: ============================================================

title Credit Risk Intelligence Platform
echo.
echo  ============================================
echo   Credit Risk Intelligence Platform
echo   Enterprise MVP - Windows Launcher
echo  ============================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Please install Python 3.10+ from https://python.org/downloads
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version

:: Check .env file exists
if not exist ".env" (
    echo.
    echo [SETUP] .env file not found. Creating from template...
    copy .env.example .env
    echo [ACTION REQUIRED] Open .env in a text editor and add your API keys.
    echo   - OPENAI_API_KEY  : https://platform.openai.com/api-keys
    echo   - GEMINI_API_KEY  : https://aistudio.google.com/app/apikey
    echo   - LANGCHAIN_API_KEY : https://smith.langchain.com (optional)
    echo.
    notepad .env
    echo Press any key when you have saved your API keys in .env...
    pause >nul
)

:: Create virtual environment if it does not exist
if not exist ".venv" (
    echo.
    echo [SETUP] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
)

:: Activate virtual environment
echo.
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

:: Install / upgrade dependencies
echo.
echo [INFO] Installing dependencies (this may take a few minutes on first run)...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    echo Check your internet connection and try again.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.

:: Launch Streamlit
echo.
echo  ============================================
echo   Starting application...
echo   Opening browser at http://localhost:8501
echo  ============================================
echo.
echo Press Ctrl+C in this window to stop the application.
echo.

streamlit run app.py --server.headless false --browser.gatherUsageStats false

pause
