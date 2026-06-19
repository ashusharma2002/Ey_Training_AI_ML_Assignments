"""
analyzer.py
-----------
Parses raw Hume.ai predictions into clean, structured emotion summaries
and generates human-readable interpretations for each model.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from config import TOP_N_EMOTIONS

logger = logging.getLogger(__name__)


# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class EmotionScore:
    name: str
    score: float   # 0.0 – 1.0

    @property
    def pct(self) -> float:
        return round(self.score * 100, 1)


@dataclass
class ModelResult:
    model_name: str                          # "face" | "prosody" | "language"
    emotions: list[EmotionScore] = field(default_factory=list)
    interpretation: str = ""
    available: bool = True                   # False if model returned no data


@dataclass
class AnalysisResult:
    video_title: str
    face: ModelResult
    prosody: ModelResult
    language: ModelResult

    def all_models(self) -> list[ModelResult]:
        return [self.face, self.prosody, self.language]


# ── Interpretation rules ──────────────────────────────────────────────────────

# Positive emotion groups used for interpretation
_POSITIVE = {
    "joy", "happiness", "excitement", "amusement", "contentment",
    "satisfaction", "admiration", "awe", "interest", "curiosity",
    "love", "pride", "relief", "gratitude", "enthusiasm",
}
_NEGATIVE = {
    "sadness", "anger", "fear", "disgust", "frustration",
    "anxiety", "distress", "contempt", "boredom", "confusion",
}
_HIGH_ENERGY = {
    "excitement", "anger", "fear", "enthusiasm", "surprise", "amusement",
}
_LOW_ENERGY = {
    "sadness", "boredom", "contentment", "relief", "tiredness",
}


def _interpret(model_name: str, top: list[EmotionScore]) -> str:
    """
    Generate a 1-3 sentence plain-English interpretation of the top emotions
    detected by a given model.
    """
    if not top:
        return "No data available for this model."

    dominant = top[0]
    top_names = {e.name.lower() for e in top[:3]}

    positives = top_names & _POSITIVE
    negatives = top_names & _NEGATIVE
    high_e = top_names & _HIGH_ENERGY
    low_e = top_names & _LOW_ENERGY

    label = {
        "face": "facial expressions",
        "prosody": "vocal tone",
        "language": "spoken language",
    }.get(model_name, model_name)

    parts: list[str] = []

    # Dominant emotion sentence
    parts.append(
        f"The strongest signal from {label} is "
        f"**{dominant.name}** ({dominant.pct}%)."
    )

    # Valence sentence
    if positives and not negatives:
        parts.append("Overall the emotional tone is positive.")
    elif negatives and not positives:
        parts.append("Overall the emotional tone is negative.")
    elif positives and negatives:
        parts.append(
            "A mix of positive and negative emotions suggests emotional complexity "
            "or contrast across the video."
        )

    # Energy sentence
    if high_e and not low_e:
        parts.append("High-energy emotions dominate, indicating an animated or intense delivery.")
    elif low_e and not high_e:
        parts.append("Low-energy emotions dominate, indicating a calm or subdued delivery.")

    # Special patterns
    if "confusion" in top_names or "interest" in top_names:
        parts.append("Signs of curiosity or critical thinking are present.")
    if "fear" in top_names and "excitement" in top_names:
        parts.append("The combination of fear and excitement may suggest suspense or anticipation.")

    return "  ".join(parts)


# ── Aggregation helpers ───────────────────────────────────────────────────────

def _aggregate_emotions(frames: list[dict[str, Any]]) -> list[EmotionScore]:
    """
    Average emotion scores across all frames/segments.
    Each frame is expected to have a list of {"name": str, "score": float} dicts
    under the key "emotions".
    """
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}

    for frame in frames:
        predictions = frame.get("predictions", [])
        for pred in predictions:
            for emotion in pred.get("emotions", []):
                name = emotion.get("name", "unknown")
                score = float(emotion.get("score", 0.0))
                totals[name] = totals.get(name, 0.0) + score
                counts[name] = counts.get(name, 0) + 1

    if not totals:
        return []

    averaged = [
        EmotionScore(name=n, score=totals[n] / counts[n])
        for n in totals
    ]
    averaged.sort(key=lambda e: e.score, reverse=True)
    return averaged[:TOP_N_EMOTIONS]


def _extract_model(source: dict[str, Any], model_key: str) -> ModelResult:
    """
    Pull out emotion data for one model from a single source's results block.
    """
    results = source.get("results", {})
    predictions_block = results.get("predictions", [])

    model_frames: list[dict] = []

    for pred in predictions_block:
        model_data = pred.get("models", {}).get(model_key, {})
        grouped = model_data.get("grouped_predictions", [])
        for group in grouped:
            model_frames.extend(group.get("predictions", []))

    if not model_frames:
        logger.warning("No data returned for model '%s'.", model_key)
        return ModelResult(
            model_name=model_key,
            available=False,
            interpretation=f"No {model_key} data was returned. "
                           "Ensure the video contains the relevant signal "
                           "(visible face, audible speech, or spoken language).",
        )

    emotions = _aggregate_emotions(model_frames)
    interp = _interpret(model_key, emotions)
    return ModelResult(model_name=model_key, emotions=emotions, interpretation=interp)


# ── Public API ────────────────────────────────────────────────────────────────

def parse_predictions(
    raw_predictions: list[dict[str, Any]],
    video_title: str = "Unknown video",
) -> AnalysisResult:
    """
    Convert raw Hume API predictions into a structured AnalysisResult.

    Parameters
    ----------
    raw_predictions : list[dict]
        The list returned by hume_client.fetch_predictions().
    video_title : str
        Human-readable title for display purposes.

    Returns
    -------
    AnalysisResult
    """
    # Hume returns one entry per source file; take the first
    source = raw_predictions[0] if raw_predictions else {}

    face_result = _extract_model(source, "face")
    prosody_result = _extract_model(source, "prosody")
    language_result = _extract_model(source, "language")

    return AnalysisResult(
        video_title=video_title,
        face=face_result,
        prosody=prosody_result,
        language=language_result,
    )
