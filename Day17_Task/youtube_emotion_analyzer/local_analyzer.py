"""
local_analyzer.py
-----------------
Local emotion analysis engine — REPLACES the discontinued Hume API.

Analyzes three modalities entirely on your machine (no API, no internet):
  • Face     — OpenCV face/smile/eye detection → emotion heuristics
  • Voice    — librosa audio features (energy, pitch, tempo) → emotion mapping
  • Language — Whisper transcription + VADER sentiment → emotion scores

Produces the SAME data shape the rest of the project expects, so
analyzer.py, visualizer.py and main.py work unchanged.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from ffmpeg_helper import FFMPEG_BIN, ensure_ffmpeg_on_path

ensure_ffmpeg_on_path()

logger = logging.getLogger(__name__)


class LocalAnalysisError(Exception):
    """Raised when local analysis fails."""


# ─────────────────────────────────────────────────────────────────────────────
# 1. FACE EMOTION  (OpenCV)
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_face(video_path: Path) -> list[dict[str, float]]:
    """Sample frames, detect faces, and infer emotion from facial features."""
    import cv2

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    smile_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_smile.xml"
    )
    eye_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_eye.xml"
    )

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.warning("Could not open video for face analysis.")
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    # Sample ~15 frames evenly across the video
    sample_count = min(15, total_frames)
    frame_indices = np.linspace(0, total_frames - 1, sample_count, dtype=int)

    frame_emotions: list[dict[str, float]] = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5,
                                              minSize=(40, 40))

        if len(faces) == 0:
            continue

        # Use the largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        roi = gray[y:y + h, x:x + w]

        smiles = smile_cascade.detectMultiScale(roi, scaleFactor=1.8, minNeighbors=20)
        eyes = eye_cascade.detectMultiScale(roi, scaleFactor=1.1, minNeighbors=10)

        emo: dict[str, float] = {}
        if len(smiles) > 0:
            emo["Joy"] = 0.72
            emo["Amusement"] = 0.55
            emo["Contentment"] = 0.48
            emo["Satisfaction"] = 0.40
        else:
            emo["Concentration"] = 0.58
            emo["Interest"] = 0.50
            emo["Calmness"] = 0.42
            emo["Contemplation"] = 0.35

        if len(eyes) >= 2:
            emo["Interest"] = emo.get("Interest", 0.0) + 0.25
            emo["Alertness"] = 0.45

        frame_emotions.append(emo)

    cap.release()
    logger.info("Face analysis: %d frames with faces.", len(frame_emotions))
    return frame_emotions


# ─────────────────────────────────────────────────────────────────────────────
# 2. VOICE EMOTION  (librosa)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_audio(video_path: Path) -> Path | None:
    """Extract audio to a temp WAV file using ffmpeg."""
    tmp = Path(tempfile.gettempdir()) / f"{video_path.stem}_audio.wav"
    cmd = [
        FFMPEG_BIN, "-y", "-i", str(video_path),
        "-ac", "1", "-ar", "22050", "-vn", str(tmp),
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return tmp if tmp.exists() else None
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning("Audio extraction failed: %s", e)
        return None


def _analyze_voice(video_path: Path) -> list[dict[str, float]]:
    """Extract audio features and map them to emotion scores."""
    import librosa

    audio_path = _extract_audio(video_path)
    if audio_path is None:
        return []

    try:
        y, sr = librosa.load(str(audio_path), sr=22050)
    except Exception as e:
        logger.warning("Could not load audio: %s", e)
        return []
    finally:
        audio_path.unlink(missing_ok=True)

    if len(y) == 0:
        return []

    # Split audio into ~2-second windows
    window = sr * 2
    segments = [y[i:i + window] for i in range(0, len(y), window) if len(y[i:i + window]) > sr // 2]

    seg_emotions: list[dict[str, float]] = []

    for seg in segments:
        rms = float(np.mean(librosa.feature.rms(y=seg)))
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(seg)))
        try:
            pitch = librosa.yin(seg, fmin=80, fmax=400, sr=sr)
            pitch_mean = float(np.nanmean(pitch))
            pitch_std = float(np.nanstd(pitch))
        except Exception:
            pitch_mean, pitch_std = 150.0, 20.0

        tempo = float(librosa.feature.tempo(y=seg, sr=sr)[0]) if len(seg) > sr else 100.0

        emo: dict[str, float] = {}

        # High energy + high pitch variation → excitement/enthusiasm
        if rms > 0.05 and pitch_std > 30:
            emo["Excitement"] = min(0.8, rms * 8)
            emo["Enthusiasm"] = min(0.7, rms * 7)
            emo["Interest"] = 0.5
        # Low energy → calmness/boredom
        elif rms < 0.02:
            emo["Calmness"] = 0.6
            emo["Boredom"] = 0.35
            emo["Tiredness"] = 0.3
        else:
            emo["Concentration"] = 0.55
            emo["Interest"] = 0.45
            emo["Determination"] = 0.38

        # High pitch → could indicate surprise/animation
        if pitch_mean > 200:
            emo["Surprise (positive)"] = 0.4
            emo["Excitement"] = emo.get("Excitement", 0.0) + 0.2

        # Fast tempo → energy
        if tempo > 120:
            emo["Excitement"] = emo.get("Excitement", 0.0) + 0.15

        seg_emotions.append(emo)

    logger.info("Voice analysis: %d audio segments.", len(seg_emotions))
    return seg_emotions


# ─────────────────────────────────────────────────────────────────────────────
# 3. LANGUAGE EMOTION  (Whisper transcription + VADER)
# ─────────────────────────────────────────────────────────────────────────────

def _transcribe(video_path: Path) -> str:
    """Transcribe speech using openai-whisper if available."""
    try:
        import whisper
    except ImportError:
        logger.info("whisper not installed — skipping transcription.")
        return ""

    audio_path = _extract_audio(video_path)
    if audio_path is None:
        return ""

    try:
        model = whisper.load_model("base")
        result = model.transcribe(str(audio_path), fp16=False)
        text = result.get("text", "").strip()
        logger.info("Transcribed %d characters.", len(text))
        return text
    except Exception as e:
        logger.warning("Transcription failed: %s", e)
        return ""
    finally:
        audio_path.unlink(missing_ok=True)


def _analyze_language(video_path: Path) -> list[dict[str, float]]:
    """Transcribe speech and run VADER sentiment → emotion scores.

    Falls back to analyzing the video filename/title when speech
    transcription (whisper) is not available or returns nothing.
    """
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    text = _transcribe(video_path)

    # Fallback: use the video title (filename) so we always have something
    if not text:
        title = video_path.stem.replace("_", " ").replace("-", " ")
        logger.info("No transcript — using video title for language analysis.")
        text = title

    if not text.strip():
        return []

    analyzer = SentimentIntensityAnalyzer()

    # Split into sentences for per-segment scoring
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    if not sentences:
        sentences = [text]

    seg_emotions: list[dict[str, float]] = []

    for sentence in sentences:
        scores = analyzer.polarity_scores(sentence)
        pos, neg, neu = scores["pos"], scores["neg"], scores["neu"]
        compound = scores["compound"]

        emo: dict[str, float] = {}
        if compound >= 0.3:
            emo["Joy"] = pos * 0.9
            emo["Satisfaction"] = pos * 0.7
            emo["Interest"] = 0.5
            emo["Excitement"] = pos * 0.6
        elif compound <= -0.3:
            emo["Sadness"] = neg * 0.8
            emo["Disappointment"] = neg * 0.6
            emo["Confusion"] = 0.4
        else:
            emo["Interest"] = 0.55
            emo["Concentration"] = 0.5
            emo["Calmness"] = neu * 0.5

        seg_emotions.append(emo)

    logger.info("Language analysis: %d sentences.", len(seg_emotions))
    return seg_emotions


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API — drop-in replacement for hume_client functions
# ─────────────────────────────────────────────────────────────────────────────

_results_cache: dict[str, Any] = {}


def submit_video(video_path: Path) -> str:
    """Run all three local analyses. Returns a fake 'job id'."""
    logger.info("Running LOCAL emotion analysis on %s", video_path.name)

    print("    • Analyzing facial expressions (OpenCV) …")
    face = _analyze_face(video_path)

    print("    • Analyzing voice tone (librosa) …")
    voice = _analyze_voice(video_path)

    print("    • Analyzing language (Whisper + VADER) …")
    language = _analyze_language(video_path)

    _results_cache["face"] = face
    _results_cache["prosody"] = voice
    _results_cache["language"] = language

    return "local-job-0001"


def poll_until_complete(job_id: str) -> None:
    """No-op — local analysis already finished in submit_video."""
    print("  ✓  Local analysis complete.")


def fetch_predictions(job_id: str) -> list[dict[str, Any]]:
    """Return results in the Hume-compatible JSON structure."""
    def _to_grouped(frame_list: list[dict[str, float]]) -> dict:
        # analyzer._aggregate_emotions expects each frame to itself contain a
        # "predictions" list, where each prediction holds an "emotions" list.
        predictions = []
        for emo_dict in frame_list:
            predictions.append({
                "predictions": [{
                    "emotions": [{"name": k, "score": v} for k, v in emo_dict.items()]
                }]
            })
        return {"grouped_predictions": [{"predictions": predictions}]}

    source = {
        "results": {
            "predictions": [{
                "models": {
                    "face": _to_grouped(_results_cache.get("face", [])),
                    "prosody": _to_grouped(_results_cache.get("prosody", [])),
                    "language": _to_grouped(_results_cache.get("language", [])),
                }
            }]
        }
    }
    return [source]
