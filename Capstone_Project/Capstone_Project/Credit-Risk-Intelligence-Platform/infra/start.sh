#!/bin/bash
# infra/start.sh — local dev startup script
set -e

echo "🏦  Credit Risk Intelligence Platform"
echo "======================================"

if [ ! -f ".env" ]; then
  echo "❌  .env file not found!"
  echo "    Run: cp .env.example .env  then fill in your API keys"
  exit 1
fi

mkdir -p data/uploads data/vectorstore/faiss_index logs data/demo

echo "✅  Starting Streamlit on http://localhost:8501"
streamlit run app.py "$@"
