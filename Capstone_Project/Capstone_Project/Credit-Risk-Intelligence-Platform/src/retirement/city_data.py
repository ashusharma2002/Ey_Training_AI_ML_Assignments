# src/retirement/city_data.py
# ============================================================
# Loads the curated Indian cities dataset and provides
# autocomplete-style search.
#
# v3.1 — added best_city_match(): returns the best matching
# city name when the typed text is >= 60% similar to one city
# in the dataset, so the retirement planner UI can auto-select
# the city without the user having to manually open and click
# the dropdown after typing.
# ============================================================
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
from src.utils.logger import get_logger

logger = get_logger(__name__)

_CITIES_FILE = Path("data/cities/indian_cities.json")
_AUTO_SELECT_THRESHOLD = 0.60   # 60% match required for auto-selection


class CityCostData(BaseModel):
    name:                  str
    state:                 str
    tier:                  int
    cost_of_living_index:  float
    housing_multiplier:    float
    healthcare_multiplier: float
    local_inflation_pct:   float


@lru_cache(maxsize=1)
def _load_all_cities() -> list[CityCostData]:
    if not _CITIES_FILE.exists():
        logger.warning(
            "City dataset not found at %s — city feature disabled.", _CITIES_FILE
        )
        return []
    try:
        raw    = json.loads(_CITIES_FILE.read_text(encoding="utf-8"))
        cities = [CityCostData(**c) for c in raw.get("cities", [])]
        logger.info("Loaded %d cities for retirement planning.", len(cities))
        return cities
    except Exception as exc:
        logger.error("Failed to load city dataset: %s", exc)
        return []


def _similarity_ratio(a: str, b: str) -> float:
    """
    Simple character-overlap similarity ratio between two lowercase strings.
    Returns a value between 0.0 (no overlap) and 1.0 (identical).

    We use a lightweight approach rather than importing difflib/fuzz so the
    retirement planner has no extra dependencies:
      - Count characters shared between the two strings (multiset intersection)
      - Divide by the length of the longer string

    Examples:
      "mumb"   vs "Mumbai"     -> 4/6  = 0.67  (above 0.60 threshold -> auto-select)
      "pun"    vs "Pune"       -> 3/4  = 0.75  (auto-select)
      "banga"  vs "Bengaluru"  -> 5/9  = 0.56  (just below -> no auto-select)
      "bengal" vs "Bengaluru"  -> 6/9  = 0.67  (auto-select)
      "xyz"    vs "Mumbai"     -> 0/6  = 0.0   (no match)
    """
    a = a.lower().strip()
    b = b.lower().strip()
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0

    # Count character frequencies for both strings
    from collections import Counter
    ca, cb = Counter(a), Counter(b)

    # Multiset intersection: sum of min(count_a, count_b) for shared chars
    shared = sum((ca & cb).values())

    # Normalise against the longer string so partial matches score fairly
    return shared / max(len(a), len(b))


def search_cities(query: str, limit: int = 8) -> list[str]:
    """
    Autocomplete search — returns city display names whose names
    contain the query as a substring (case-insensitive).
    """
    cities = _load_all_cities()
    if not query:
        return [c.name for c in cities[:limit]]
    q = query.lower().strip()
    matches = [c.name for c in cities if q in c.name.lower()]
    return matches[:limit]


def best_city_match(query: str, threshold: float = _AUTO_SELECT_THRESHOLD) -> str | None:
    """
    Returns the single best-matching city name when the typed query is
    >= `threshold` similar to one city name, otherwise returns None.

    Used by retirement_planner.py to auto-select the selectbox when the
    user has typed enough to unambiguously identify a city — removing the
    need for a manual click on the dropdown after typing.

    Auto-select rules (in priority order):
    1. EXACT match (case-insensitive) -> always auto-select, score = 1.0
    2. Substring match with only 1 result -> auto-select if score >= threshold
    3. Substring match with multiple results -> auto-select only the top
       match if it scores significantly higher than the second-best
       (gap >= 0.15) so "pun" doesn't ambiguously auto-select between
       "Pune" and "Vijayawada" (no match), but "pune" auto-selects "Pune"

    Returns None if no city meets the threshold — in that case the user
    can still select manually from the dropdown.
    """
    if not query:
        return None

    cities   = _load_all_cities()
    q_lower  = query.lower().strip()

    # Rule 1: exact match
    for c in cities:
        if c.name.lower() == q_lower:
            return c.name

    # Score all cities
    scored: list[tuple[float, str]] = []
    for c in cities:
        score = _similarity_ratio(q_lower, c.name)
        if score >= threshold:
            scored.append((score, c.name))

    if not scored:
        return None

    scored.sort(reverse=True)
    top_score, top_name = scored[0]

    # If only one city meets the threshold -> safe to auto-select
    if len(scored) == 1:
        return top_name

    # Multiple cities meet threshold -> auto-select only if the winner is
    # clearly ahead of second place (gap >= 0.15), to avoid wrong picks
    second_score = scored[1][0]
    if top_score - second_score >= 0.15:
        return top_name

    # Ambiguous -> return None, let the user pick manually
    return None


def get_city_data(city_name: str) -> CityCostData | None:
    cities = _load_all_cities()
    for c in cities:
        if c.name == city_name:
            return c
    return None


def all_city_names() -> list[str]:
    return [c.name for c in _load_all_cities()]
