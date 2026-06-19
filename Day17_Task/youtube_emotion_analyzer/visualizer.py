"""
visualizer.py
-------------
Two output modes:
  1. Terminal — rich colour-coded text report with ASCII bars
  2. Chart     — matplotlib bar charts saved as PNG (one panel per model)
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from config import CHART_COLORS, OUTPUT_DIR, TOP_N_EMOTIONS

if TYPE_CHECKING:
    from analyzer import AnalysisResult, ModelResult

logger = logging.getLogger(__name__)

# ── ANSI colour codes (gracefully degrade if terminal doesn't support them) ──

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"

_PURPLE = "\033[38;5;141m"
_TEAL   = "\033[38;5;79m"
_CORAL  = "\033[38;5;209m"
_YELLOW = "\033[38;5;220m"
_WHITE  = "\033[97m"

_MODEL_COLOURS = {
    "face":     _PURPLE,
    "prosody":  _TEAL,
    "language": _CORAL,
}

_MODEL_LABELS = {
    "face":     "Facial Expressions",
    "prosody":  "Vocal Tone (Prosody)",
    "language": "Language / Speech",
}

BAR_WIDTH = 30  # characters for the ASCII bar


# ── Terminal display ──────────────────────────────────────────────────────────

def _ascii_bar(score: float, width: int = BAR_WIDTH) -> str:
    filled = round(score * width)
    return "█" * filled + "░" * (width - filled)


def _print_model(result: "ModelResult") -> None:
    colour = _MODEL_COLOURS.get(result.model_name, _WHITE)
    label  = _MODEL_LABELS.get(result.model_name, result.model_name.title())

    print(f"\n{colour}{_BOLD}{'─' * 60}{_RESET}")
    print(f"{colour}{_BOLD}  {label}{_RESET}")
    print(f"{colour}{_BOLD}{'─' * 60}{_RESET}")

    if not result.available:
        print(f"  {_DIM}{result.interpretation}{_RESET}")
        return

    # Emotion bars
    for emo in result.emotions:
        bar  = _ascii_bar(emo.score)
        name = emo.name.capitalize().ljust(20)
        pct  = f"{emo.pct:>5.1f}%"
        print(f"  {colour}{name}{_RESET}  {bar}  {_YELLOW}{pct}{_RESET}")

    # Interpretation
    print(f"\n  {_DIM}Interpretation:{_RESET}")
    # Strip markdown bold markers for terminal
    clean = result.interpretation.replace("**", _BOLD).replace("**", _RESET)
    # Simple word-wrap at 72 chars
    words = clean.split()
    line  = "  "
    for word in words:
        if len(line) + len(word) + 1 > 74:
            print(line)
            line = "  " + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line)


def print_report(result: "AnalysisResult") -> None:
    """Print a full colour-coded emotion report to stdout."""
    width = 62
    print(f"\n{'═' * width}")
    print(f"{'YouTube Emotion Analysis Report':^{width}}")
    print(f"{'═' * width}")
    print(f"  {_BOLD}Video:{_RESET} {result.video_title}")
    print(f"  {_DIM}Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{_RESET}")
    print(f"{'═' * width}")

    for model in result.all_models():
        _print_model(model)

    print(f"\n{'═' * width}")
    print(f"  {_DIM}Top {TOP_N_EMOTIONS} emotions per model shown.{_RESET}")
    print(f"{'═' * width}\n")


# ── Matplotlib chart ──────────────────────────────────────────────────────────

def save_chart(result: "AnalysisResult") -> Path:
    """
    Generate a 3-panel horizontal bar chart and save it to OUTPUT_DIR.

    Returns
    -------
    Path
        Path to the saved PNG file.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")        # headless / no GUI needed
        import matplotlib.pyplot as plt
        import matplotlib.patheffects as pe
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required for chart output. "
            "Run: pip install matplotlib"
        ) from exc

    available_models = [m for m in result.all_models() if m.available and m.emotions]
    n_panels = len(available_models)

    if n_panels == 0:
        logger.warning("No model data available — skipping chart.")
        return None

    fig, axes = plt.subplots(
        1, n_panels,
        figsize=(7 * n_panels, 7),
        facecolor="#1a1a2e",
    )

    if n_panels == 1:
        axes = [axes]

    # plt.suptitle(
    #     f"Emotion Analysis — {result.video_title[:60]}",
    safe_chart_title = result.video_title.encode("ascii", "ignore").decode("ascii").strip()
    if not safe_chart_title:
        safe_chart_title = "Video"
    plt.suptitle(
        f"Emotion Analysis — {safe_chart_title[:60]}",
        color="white",
        fontsize=13,
        fontweight="bold",
        y=1.01,
    )

    for ax, model in zip(axes, available_models):
        colour = CHART_COLORS.get(model.model_name, "#888888")
        label  = _MODEL_LABELS.get(model.model_name, model.model_name.title())

        names  = [e.name.capitalize() for e in model.emotions]
        scores = [e.pct for e in model.emotions]

        # Horizontal bars (highest score at top)
        bars = ax.barh(
            names[::-1],
            scores[::-1],
            color=colour,
            edgecolor="none",
            height=0.65,
        )

        # Score labels on bars
        for bar, score in zip(bars, scores[::-1]):
            x_pos = bar.get_width() + 0.5
            ax.text(
                x_pos, bar.get_y() + bar.get_height() / 2,
                f"{score:.1f}%",
                va="center", ha="left",
                color="white", fontsize=9,
                path_effects=[pe.withStroke(linewidth=2, foreground="#1a1a2e")],
            )

        ax.set_title(label, color=colour, fontsize=11, fontweight="bold", pad=10)
        ax.set_xlabel("Score (%)", color="#aaaaaa", fontsize=9)
        ax.set_xlim(0, max(scores) * 1.25 + 2)
        ax.tick_params(colors="white", labelsize=9)
        ax.spines[["top", "right", "bottom"]].set_visible(False)
        ax.spines["left"].set_color("#444444")
        ax.set_facecolor("#1a1a2e")
        ax.xaxis.label.set_color("#aaaaaa")
        ax.tick_params(axis="x", colors="#aaaaaa")

    plt.tight_layout()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in "_ -" else "_" for c in result.video_title)[:40]
    out_path = OUTPUT_DIR / f"emotions_{safe_title}_{timestamp}.png"

    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

    logger.info("Chart saved: %s", out_path)
    return out_path
