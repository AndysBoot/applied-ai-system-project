"""
Real-song ingestion from the MusicBrainz API.

MusicBrainz gives real title/artist/genre-tag metadata for actual recordings,
but it has no audio-analysis data at all -- no energy, valence, danceability,
acousticness, or tempo. Those numeric fields are what recommender.score_song()
actually scores against, so they can't just be left out.

Since there is no way to measure them per-song without running audio
analysis ourselves, GENRE_FEATURE_ESTIMATES below encodes a rough, documented
estimate per genre (typical energy/valence/danceability/acousticness/tempo
for that genre, e.g. "metal" skews high-energy/low-valence/low-acousticness).
Each song's estimate is nudged by a small deterministic offset derived from
its MusicBrainz ID, so same-genre songs don't all land on an identical point,
but the same song always gets the same estimate on re-import.

A recording with no recognizable genre tag is skipped entirely rather than
guessing blind -- there's nothing to base even a rough estimate on.
"""

import hashlib
import logging
import time
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

API_BASE = "https://musicbrainz.org/ws/2"
USER_AGENT = "AppliedAISystemProject/1.0 (contact: andysosa2007@gmail.com)"
REQUEST_TIMEOUT = 15
PAGE_SIZE = 100  # MusicBrainz's hard max results-per-request
RATE_LIMIT_SECONDS = 1.1  # MusicBrainz asks for max ~1 request/sec without special arrangement

# genre -> (energy, valence, danceability, acousticness, tempo_bpm, mood)
# Deliberately rough, genre-level stereotypes -- not measurements. Values are
# starting points; JITTER_RANGE below perturbs them per song.
GENRE_FEATURE_ESTIMATES: Dict[str, tuple] = {
    "rock":        (0.75, 0.55, 0.60, 0.20, 130, "energetic"),
    "classic rock":(0.72, 0.55, 0.55, 0.25, 122, "energetic"),
    "pop":         (0.70, 0.70, 0.75, 0.20, 118, "happy"),
    "indie pop":   (0.65, 0.72, 0.70, 0.30, 116, "happy"),
    "metal":       (0.92, 0.30, 0.55, 0.08, 150, "aggressive"),
    "punk":        (0.90, 0.40, 0.55, 0.10, 165, "aggressive"),
    "jazz":        (0.40, 0.65, 0.55, 0.75, 95,  "relaxed"),
    "classical":   (0.25, 0.55, 0.20, 0.95, 85,  "peaceful"),
    "ambient":     (0.20, 0.55, 0.30, 0.85, 65,  "chill"),
    "electronic":  (0.80, 0.60, 0.80, 0.10, 126, "energetic"),
    "techno":      (0.85, 0.50, 0.80, 0.08, 128, "energetic"),
    "house":       (0.80, 0.65, 0.85, 0.10, 124, "energetic"),
    "synthwave":   (0.70, 0.50, 0.70, 0.20, 110, "moody"),
    "hip hop":     (0.68, 0.55, 0.80, 0.15, 95,  "groovy"),
    "hip-hop":     (0.68, 0.55, 0.80, 0.15, 95,  "groovy"),
    "rap":         (0.70, 0.50, 0.78, 0.12, 98,  "groovy"),
    "r&b":         (0.55, 0.60, 0.70, 0.35, 90,  "romantic"),
    "soul":        (0.55, 0.62, 0.65, 0.40, 92,  "romantic"),
    "funk":        (0.72, 0.65, 0.82, 0.20, 110, "groovy"),
    "disco":       (0.78, 0.72, 0.85, 0.15, 120, "happy"),
    "folk":        (0.35, 0.55, 0.45, 0.85, 92,  "nostalgic"),
    "country":     (0.50, 0.55, 0.55, 0.65, 100, "melancholic"),
    "blues":       (0.40, 0.45, 0.45, 0.60, 85,  "melancholic"),
    "reggae":      (0.55, 0.65, 0.70, 0.40, 90,  "chill"),
    "lofi":        (0.35, 0.55, 0.55, 0.70, 78,  "chill"),
    "lo-fi":       (0.35, 0.55, 0.55, 0.70, 78,  "chill"),
    "gospel":      (0.55, 0.65, 0.50, 0.55, 90,  "uplifting"),
}

JITTER_RANGE = 0.06  # +/- fractional nudge applied to each of the 4 [0,1] features


def _deterministic_jitter(seed_key: str, salt: str) -> float:
    """Stable pseudo-random offset in [-JITTER_RANGE, JITTER_RANGE], keyed by seed_key+salt."""
    digest = hashlib.md5(f"{seed_key}:{salt}".encode()).hexdigest()
    fraction = int(digest[:8], 16) / 0xFFFFFFFF  # -> [0, 1]
    return (fraction * 2 - 1) * JITTER_RANGE


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def resolve_genre(tags: List[Dict]) -> Optional[str]:
    """Pick the first tag (by vote count) that matches a genre we have estimates for."""
    for tag in sorted(tags, key=lambda t: t.get("count", 0), reverse=True):
        name = tag.get("name", "").strip().lower()
        if name in GENRE_FEATURE_ESTIMATES:
            return name
    return None


def estimate_features(genre: str, mbid: str) -> Dict:
    """Rough genre-level estimate for the numeric scoring fields, nudged per-song by mbid."""
    energy, valence, danceability, acousticness, _, mood = GENRE_FEATURE_ESTIMATES[genre]
    return {
        "genre": genre,
        "mood": mood,
        "energy": round(_clamp01(energy + _deterministic_jitter(mbid, "energy")), 2),
        "valence": round(_clamp01(valence + _deterministic_jitter(mbid, "valence")), 2),
        "danceability": round(_clamp01(danceability + _deterministic_jitter(mbid, "danceability")), 2),
        "acousticness": round(_clamp01(acousticness + _deterministic_jitter(mbid, "acousticness")), 2),
    }


def _fetch_page(genre: str, offset: int, page_size: int) -> List[Dict]:
    response = requests.get(
        f"{API_BASE}/recording",
        params={"query": f'tag:"{genre}"', "fmt": "json", "limit": page_size, "offset": offset, "inc": "tags"},
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("recordings", [])


def fetch_recordings_by_genre(genre: str, limit: int = 25, seen_keys: Optional[set] = None) -> List[Dict]:
    """
    Query MusicBrainz for real recordings tagged with `genre`, up to `limit` songs.

    Paginates in PAGE_SIZE (100, MusicBrainz's hard per-request max) chunks, sleeping
    RATE_LIMIT_SECONDS between requests per their API etiquette. Returns song dicts
    (title, artist, genre, mood, energy, valence, danceability, acousticness)
    ready for src.db.add_song -- one per recording that has a resolvable genre tag.
    Recordings with no recognizable genre tag are skipped (logged), since there's
    no basis for even a rough estimate.

    seen_keys: an optional set of (title.lower(), artist.lower()) tuples, shared
    across multiple calls (e.g. across genres in a bulk import), to skip
    duplicate recordings of the same song. Mutated in place.
    """
    if seen_keys is None:
        seen_keys = set()

    songs: List[Dict] = []
    skipped = 0
    offset = 0

    while len(songs) < limit:
        page_size = min(PAGE_SIZE, limit - len(songs) + 20)  # pad a bit to absorb skips
        recordings = _fetch_page(genre, offset, page_size)
        if not recordings:
            break  # exhausted MusicBrainz's results for this tag

        for rec in recordings:
            if len(songs) >= limit:
                break

            artist_credit = rec.get("artist-credit") or []
            if not artist_credit or not rec.get("title"):
                skipped += 1
                continue

            key = (rec["title"].strip().lower(), artist_credit[0]["name"].strip().lower())
            if key in seen_keys:
                skipped += 1
                continue

            resolved_genre = resolve_genre(rec.get("tags", []))
            if resolved_genre is None:
                skipped += 1
                continue

            seen_keys.add(key)
            estimate = estimate_features(resolved_genre, rec["id"])
            songs.append({
                "title": rec["title"],
                "artist": artist_credit[0]["name"],
                **estimate,
            })

        offset += len(recordings)
        if len(recordings) < page_size:
            break  # last page was partial -- no more results available

        if len(songs) < limit:
            time.sleep(RATE_LIMIT_SECONDS)

    if skipped:
        logger.info("skipped %d recordings (duplicate or no resolvable genre tag) for '%s'", skipped, genre)

    return songs
