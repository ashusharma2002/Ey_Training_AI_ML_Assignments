"""
main.py
-------
Entry point for the YouTube Emotion Analysis Tool.

Usage
-----
    python main.py <youtube_url>
    python main.py <youtube_url> --no-chart
    python main.py <youtube_url> --keep-video
    python main.py --help

Examples
--------
    python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    python main.py "https://www.youtube.com/shorts/abc123" --no-chart
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# ── Project imports ───────────────────────────────────────────────────────────
from downloader import download_video
from local_analyzer import (
    LocalAnalysisError,
    fetch_predictions,
    poll_until_complete,
    submit_video,
)
from analyzer import parse_predictions
from visualizer import print_report, save_chart


# ── Logging setup ─────────────────────────────────────────────────────────────

def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        format="%(levelname)s | %(name)s | %(message)s",
        level=level,
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="youtube_emotion_analyzer",
        description="Analyse emotions in a YouTube video using local AI (offline, no API).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "url",
        help="Full YouTube URL (video or Short).",
    )
    parser.add_argument(
        "--no-chart",
        action="store_true",
        default=False,
        help="Skip generating the matplotlib PNG chart.",
    )
    parser.add_argument(
        "--keep-video",
        action="store_true",
        default=False,
        help="Keep the downloaded video file after analysis (deleted by default).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="Enable debug logging.",
    )
    return parser


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run(url: str, no_chart: bool = False, keep_video: bool = False) -> int:
    """
    Execute the full analysis pipeline.

    Returns
    -------
    int
        Exit code (0 = success, 1 = error).
    """
    video_path: Path | None = None

    try:
        # 1. Download video
        print("\n🎬  YouTube Emotion Analyzer (local mode — no API needed)\n")

        # 2. Download video
        print(f"📥  Downloading video …\n    {url}")
        video_path = download_video(url)
        video_title = video_path.stem.replace("_", " ")
        print(f"    ✓  Saved: {video_path.name}  ({video_path.stat().st_size / 1e6:.1f} MB)\n")

        # 3. Run local analysis
        print("🧠  Running local emotion analysis …")
        job_id = submit_video(video_path)
        print()

        # 4. Finalize
        poll_until_complete(job_id)
        print()

        # 5. Gather results
        raw = fetch_predictions(job_id)

        # 6. Parse + interpret
        result = parse_predictions(raw, video_title=video_title)

        # 7. Print terminal report
        print_report(result)

        # 8. Save chart (unless skipped)
        if not no_chart:
            print("🎨  Generating emotion chart …")
            chart_path = save_chart(result)
            if chart_path:
                print(f"    ✓  Chart saved: {chart_path}\n")

        return 0

    except EnvironmentError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 1

    except LocalAnalysisError as exc:
        print(f"\n[Analysis Error] {exc}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n\n  Interrupted by user.", file=sys.stderr)
        return 1

    except Exception as exc:  # noqa: BLE001
        print(f"\n[Unexpected Error] {exc}", file=sys.stderr)
        logging.exception("Unhandled exception in pipeline")
        return 1

    finally:
        # Clean up the downloaded video unless --keep-video was passed
        if video_path and video_path.exists() and not keep_video:
            video_path.unlink()
            logging.debug("Deleted downloaded video: %s", video_path)


# ── Entry ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    _setup_logging(args.verbose)
    sys.exit(run(args.url, no_chart=args.no_chart, keep_video=args.keep_video))


if __name__ == "__main__":
    main()
