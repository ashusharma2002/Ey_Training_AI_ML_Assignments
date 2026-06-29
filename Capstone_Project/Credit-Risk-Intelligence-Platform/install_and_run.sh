#!/bin/bash
# ============================================================
# Credit Risk Intelligence Platform — Mac/Linux Launcher
# Run with:  bash install_and_run.sh
# Or make executable:  chmod +x install_and_run.sh && ./install_and_run.sh
# Requirements: Python 3.10, 3.11, or 3.12
# ============================================================

set -e

echo ""
echo "============================================"
echo " Credit Risk Intelligence Platform"
echo " Enterprise MVP - Mac/Linux Launcher"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found."
    echo "Install from https://python.org/downloads"
    echo "Mac: brew install python3"
    echo "Ubuntu: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[OK] Python $PYTHON_VERSION found."

# Check .env
if [ ! -f ".env" ]; then
    echo ""
    echo "[SETUP] .env file not found. Creating from template..."
    cp .env.example .env
    echo "[ACTION REQUIRED] Edit .env and add your API keys:"
    echo "  - OPENAI_API_KEY   : https://platform.openai.com/api-keys"
    echo "  - GEMINI_API_KEY   : https://aistudio.google.com/app/apikey"
    echo "  - LANGCHAIN_API_KEY: https://smith.langchain.com (optional)"
    echo ""
    echo "Opening .env in nano editor... (Ctrl+X to save and exit)"
    sleep 2
    nano .env || vi .env || echo "Please edit .env manually then re-run this script."
fi

# Create venv
if [ ! -d ".venv" ]; then
    echo ""
    echo "[SETUP] Creating virtual environment..."
    python3 -m venv .venv
    echo "[OK] Virtual environment created."
fi

# Activate venv
echo ""
echo "[INFO] Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo ""
echo "[INFO] Installing dependencies (first run may take a few minutes)..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "[OK] Dependencies installed."

# Launch
echo ""
echo "============================================"
echo " Starting application..."
echo " Opening at http://localhost:8501"
echo "============================================"
echo ""
echo "Press Ctrl+C to stop the application."
echo ""

streamlit run app.py --server.headless false --browser.gatherUsageStats false
