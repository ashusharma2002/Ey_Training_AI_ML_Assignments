"""
ffmpeg_helper.py
----------------
Locates the ffmpeg executable even when it isn't on the system PATH.

Search order:
  1. PATH (normal case — `ffmpeg` works directly)
  2. Common winget install location (Windows)
  3. Common manual install locations
  4. FFMPEG_PATH environment variable (manual override)

Exposes:
  • FFMPEG_DIR  — directory containing ffmpeg.exe (or None)
  • FFMPEG_BIN  — full path to ffmpeg executable (or "ffmpeg" as fallback)
  • ensure_ffmpeg_on_path()  — prepends FFMPEG_DIR to os.environ PATH
"""

import os
import shutil
from pathlib import Path

# 1. Manual override via env var
_env_override = os.environ.get("FFMPEG_PATH", "").strip()

# 2. Build list of candidate directories to search
_candidates: list[Path] = []

if _env_override:
    _candidates.append(Path(_env_override))

# Windows winget location (glob for any version)
_localappdata = os.environ.get("LOCALAPPDATA", "")
if _localappdata:
    winget_base = Path(_localappdata) / "Microsoft" / "WinGet" / "Packages"
    if winget_base.exists():
        # Find any Gyan.FFmpeg .../bin folder
        for match in winget_base.glob("Gyan.FFmpeg*/**/bin"):
            _candidates.append(match)

# Common manual install paths
_candidates += [
    Path(r"C:\ffmpeg\bin"),
    Path(r"C:\Program Files\ffmpeg\bin"),
    Path("/usr/bin"),
    Path("/usr/local/bin"),
    Path("/opt/homebrew/bin"),
]


def _find_ffmpeg() -> tuple[str | None, str]:
    """Return (directory, full_executable_path)."""
    # 1. Already on PATH?
    on_path = shutil.which("ffmpeg")
    if on_path:
        return str(Path(on_path).parent), on_path

    # 2. Search candidates
    exe_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    for d in _candidates:
        exe = d / exe_name
        if exe.exists():
            return str(d), str(exe)

    # 3. Not found — fall back to bare name (will error clearly later)
    return None, "ffmpeg"


FFMPEG_DIR, FFMPEG_BIN = _find_ffmpeg()


def ensure_ffmpeg_on_path() -> None:
    """Prepend the located ffmpeg directory to PATH for this process."""
    if FFMPEG_DIR and FFMPEG_DIR not in os.environ.get("PATH", ""):
        os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")


def ffmpeg_available() -> bool:
    """True if a usable ffmpeg was located."""
    return FFMPEG_DIR is not None
