# YouTube Emotion Analyzer 🎬😊

Analyse emotions in any YouTube video or Short — **fully offline, no API key needed.**

> **Note:** This project originally used Hume.ai's Expression Measurement API, which was
> **permanently discontinued on June 14, 2026.** It has been rebuilt to run emotion
> analysis locally on your machine using open-source libraries.

Detects emotions from three sources:

| Model | Library | What it reads |
|---|---|---|
| 😐 **Face** | OpenCV | Facial expressions (smile / eyes) across video frames |
| 🗣️ **Voice** | librosa | Vocal energy, pitch, and tempo → emotional tone |
| 💬 **Language** | VADER (+ optional Whisper) | Sentiment of spoken words / title |

Outputs a colour-coded **terminal report** and a **PNG bar chart**.

---

## Prerequisites

- Python **3.11** (3.9–3.12 supported)
- **ffmpeg** installed (for audio extraction + video download)

### Install ffmpeg

| OS | Command |
|---|---|
| Windows | `winget install ffmpeg` |
| macOS | `brew install ffmpeg` |
| Ubuntu/Debian | `sudo apt install ffmpeg` |

---

## Setup

```bash
# 1. Create & activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate        # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt
```

No API key or `.env` file is required anymore.

---

## Usage

```bash
python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
python main.py "https://www.youtube.com/shorts/SHORT_ID"
```

### Options

```bash
python main.py "URL" --no-chart      # Terminal report only, skip PNG
python main.py "URL" --keep-video    # Keep the downloaded video
python main.py "URL" --verbose       # Show debug logs
python main.py --help
```

### Optional: real speech transcription

By default, language analysis uses the video title. For real speech-to-text
(analysing what is actually said), install Whisper:

```bash
pip install openai-whisper
```

The tool will automatically use it when available.

---

## Output

- **Terminal report** — colour-coded ASCII bars + plain-English interpretation per model
- **PNG chart** — saved to `output/emotions_<title>_<timestamp>.png`

---

## How it works

```
YouTube URL
    │
    ▼
[downloader.py]  yt-dlp downloads the video
    │
    ▼
[local_analyzer.py]  runs three analyses locally:
    ├── Face     → OpenCV detects faces, smiles, eyes
    ├── Voice    → librosa extracts energy/pitch/tempo from audio
    └── Language → VADER scores sentiment of transcript/title
    │
    ▼
[analyzer.py]  aggregates scores + writes interpretations
    │
    ▼
[visualizer.py]  prints report + saves PNG chart
```

---

## Project structure

```
youtube_emotion_analyzer/
├── main.py              # CLI entry point
├── config.py            # Settings
├── downloader.py        # yt-dlp wrapper
├── local_analyzer.py    # ⭐ Local emotion engine (replaces Hume API)
├── analyzer.py          # Aggregates scores + interpretations
├── visualizer.py        # Terminal report + matplotlib chart
├── requirements.txt
├── .gitignore
├── README.md
└── .vscode/launch.json
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ffmpeg not found` | Install ffmpeg, restart terminal |
| No face data | Video may have no clear/frontal faces — normal |
| No voice data | Video may have no audio track |
| yt-dlp download fails | `pip install -U yt-dlp` |
| Want real speech analysis | `pip install openai-whisper` |

---

## License

MIT
