"""
config.py
---------
Loads environment variables and centralises all project settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


def get_api_key() -> str:
    """Return the Hume API key, raising clearly if missing."""
    key = os.getenv("HUME_API_KEY", "").strip()
    if not key:
        raise EnvironmentError(
            "\n[ERROR] HUME_API_KEY is not set.\n"
            "  1. Copy .env.example  →  .env\n"
            "  2. Paste your key from https://beta.hume.ai → Settings → Profile\n"
        )
    return key


# ── Hume API settings ─────────────────────────────────────────────────────────
HUME_BASE_URL = "https://api.hume.ai/v0"
JOB_POLL_INTERVAL_SEC = 5      # seconds between status checks
JOB_TIMEOUT_SEC = 300          # give up after 5 minutes

# ── Models to request ─────────────────────────────────────────────────────────
# All three: face expression, speech prosody, language sentiment
HUME_MODELS = {
    "face": {},
    "prosody": {},
    "language": {},
}

# ── Download settings ─────────────────────────────────────────────────────────
DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# yt-dlp format: best video+audio, capped at 720p to keep file sizes manageable
YTDLP_FORMAT = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"

# ── Output settings ───────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Top-N emotions to display per model
TOP_N_EMOTIONS = 10

# Colour palette for matplotlib charts (one per model)
CHART_COLORS = {
    "face":     "#7F77DD",   # purple
    "prosody":  "#1D9E75",   # teal
    "language": "#D85A30",   # coral
}
