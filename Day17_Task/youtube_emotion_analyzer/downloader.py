"""
downloader.py
-------------
Downloads a YouTube video (or Short) using yt-dlp and returns the local path.
"""

import re
import time
import logging
from pathlib import Path

import yt_dlp

from config import DOWNLOAD_DIR, YTDLP_FORMAT
from ffmpeg_helper import FFMPEG_DIR, ensure_ffmpeg_on_path

# Make sure ffmpeg is reachable for this process
ensure_ffmpeg_on_path()

logger = logging.getLogger(__name__)


def _sanitise_filename(title: str) -> str:
    """Replace characters that are unsafe in file names."""
    return re.sub(r'[\\/*?:"<>|]', "_", title)[:80]


def download_video(url: str) -> Path:
    """
    Download a YouTube video to DOWNLOAD_DIR.

    Parameters
    ----------
    url : str
        Full YouTube URL (video or Short).

    Returns
    -------
    Path
        Absolute path to the downloaded file.

    Raises
    ------
    RuntimeError
        If yt-dlp fails to download or locate the file.
    """
    logger.info("Starting download: %s", url)

    # Collect the final filename from yt-dlp's postprocessor hooks
    downloaded_files: list[str] = []

    def _progress_hook(d: dict) -> None:
        if d["status"] == "downloading":
            pct = d.get("_percent_str", "?").strip()
            speed = d.get("_speed_str", "?").strip()
            print(f"\r  Downloading … {pct}  @ {speed}    ", end="", flush=True)
        elif d["status"] == "finished":
            print()  # newline after progress bar
            downloaded_files.append(d["filename"])
            logger.debug("Downloaded chunk: %s", d["filename"])

    ydl_opts = {
        "format": YTDLP_FORMAT,
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
        "progress_hooks": [_progress_hook],
        "quiet": True,
        "no_warnings": False,
        "merge_output_format": "mp4",
        # Retry on transient network errors
        "retries": 3,
        "fragment_retries": 3,
    }

    # Tell yt-dlp exactly where ffmpeg lives (in case it isn't on PATH)
    if FFMPEG_DIR:
        ydl_opts["ffmpeg_location"] = FFMPEG_DIR

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            raise RuntimeError(f"yt-dlp returned no info for URL: {url}")

        # yt-dlp sometimes merges files; the final path is in info["requested_downloads"]
        try:
            final_path = Path(
                ydl.prepare_filename(info["requested_downloads"][0])
            ).with_suffix(".mp4")
        except (KeyError, IndexError):
            # Fallback: reconstruct from title + ext
            title = _sanitise_filename(info.get("title", "video"))
            ext = info.get("ext", "mp4")
            final_path = DOWNLOAD_DIR / f"{title}.{ext}"

    # Give the OS a moment to finish flushing the file
    time.sleep(0.5)

    if not final_path.exists():
        # Last resort: pick the most recently modified mp4 in DOWNLOAD_DIR
        candidates = sorted(
            DOWNLOAD_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if candidates:
            final_path = candidates[0]
        else:
            raise RuntimeError(
                f"Download appeared to succeed but file not found at {final_path}"
            )

    logger.info("Video saved to: %s  (%.1f MB)", final_path, final_path.stat().st_size / 1e6)
    return final_path
