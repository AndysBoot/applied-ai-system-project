from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import csv
import logging
from pathlib import Path

from src.guardrails import validate_profile

logger = logging.getLogger(__name__)

# Beyond its tolerance band, a feature's score decays linearly down to this
# floor over an equal-width band, instead of instantly cliffing from full
# score to half score the moment the tolerance is exceeded.
TOLERANCE_FLOOR_FRACTION = 0.5


@dataclass
class RecommendationResult:
    """Bundles ranked recommendations with any guardrail warnings raised for the profile."""
    items: List[Tuple[Dict, float, str, List[str]]]
    warnings: List[str] = field(default_factory=list)


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    print(f"Loading songs from {csv_path}...")

    # Resolve path relative to this script's directory
    script_dir = Path(__file__).parent.parent
    full_path = script_dir / csv_path

    songs = []
    with open(full_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Convert numerical fields to appropriate types
            song = {
                'id': int(row['id']),
                'title': row['title'],
                'artist': row['artist'],
                'genre': row['genre'],
                'mood': row['mood'],
                'energy': float(row['energy']),
                'tempo_bpm': float(row['tempo_bpm']),
                'valence': float(row['valence']),
                'danceability': float(row['danceability']),
                'acousticness': float(row['acousticness'])
            }
            songs.append(song)
    return songs

def _tolerance_band_score(weight: float, base_value: float, diff: float, tolerance: float) -> float:
    """Score a numerical feature with a smoothed tolerance band instead of a hard cliff.

    Within the tolerance band (diff <= tolerance) the feature scores full marks,
    same as before. Beyond it, instead of instantly dropping to the floor, the
    score decays linearly over an equal-width band and only reaches the floor
    once the song is twice as far off as the tolerance allows. This fixes the
    "cliff" behavior flagged in model_card.md, while leaving the score at
    diff=0 and diff=tolerance unchanged from the original implementation.
    """
    if diff <= tolerance:
        fraction = 1.0
    else:
        decay_width = max(tolerance, 1e-9)
        overshoot = diff - tolerance
        if overshoot >= decay_width:
            fraction = TOLERANCE_FLOOR_FRACTION
        else:
            fraction = 1.0 - (1.0 - TOLERANCE_FLOOR_FRACTION) * (overshoot / decay_width)
    return weight * base_value * fraction


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a single song against user preferences, returning (score, reasons)."""
    score = 0.0
    reasons = []

    # Genre Matching
    if song['genre'] == user_prefs.get('favorite_genre'):
        score += 2.0
        reasons.append("genre match (+2.0)")

    # Mood Matching
    if song['mood'] == user_prefs.get('favorite_mood'):
        score += 1.5
        reasons.append("mood match (+1.5)")

    # Numerical Feature Scoring
    feature_weights = user_prefs.get('feature_weights', {
        'valence': 0.30,
        'energy': 0.25,
        'danceability': 0.15
    })
    default_tolerance = user_prefs.get('tolerance', 0.2)
    base_value = 8.0

    # Valence (happiness) -- uses valence_tolerance if set, else falls back to
    # the generic 'tolerance' key (previously this fallback never triggered
    # because per-feature tolerance keys were ignored entirely).
    target_valence = user_prefs.get('target_valence', 0.5)
    valence_diff = abs(song['valence'] - target_valence)
    valence_tolerance = user_prefs.get('valence_tolerance', default_tolerance)
    valence_score = _tolerance_band_score(feature_weights.get('valence', 0.0), base_value, valence_diff, valence_tolerance)
    score += valence_score
    reasons.append(f"valence within range (+{valence_score:.1f})")

    # Energy
    target_energy = user_prefs.get('target_energy', 0.5)
    energy_diff = abs(song['energy'] - target_energy)
    energy_tolerance = user_prefs.get('energy_tolerance', default_tolerance)
    energy_score = _tolerance_band_score(feature_weights.get('energy', 0.0), base_value, energy_diff, energy_tolerance)
    score += energy_score
    reasons.append(f"energy within range (+{energy_score:.1f})")

    # Danceability
    target_danceability = user_prefs.get('target_danceability', 0.5)
    danceability_diff = abs(song['danceability'] - target_danceability)
    danceability_tolerance = user_prefs.get('danceability_tolerance', default_tolerance)
    danceability_score = _tolerance_band_score(feature_weights.get('danceability', 0.0), base_value, danceability_diff, danceability_tolerance)
    score += danceability_score
    reasons.append(f"danceability within range (+{danceability_score:.1f})")

    # Acousticness Bonus
    if user_prefs.get('likes_acoustic', False) and song['acousticness'] > 0.7:
        acoustic_score = user_prefs.get('acoustic_preference_strength', 1.0)
        score += acoustic_score
        reasons.append(f"acoustic bonus (+{acoustic_score:.1f})")

    return (score, reasons)


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> RecommendationResult:
    """Recommend top k songs ranked by score, filtering negative genres.

    Runs the guardrail layer first (logged, non-blocking), then scores every
    song. If the negative-genre filter would eliminate the entire catalog, it
    falls back to scoring the unfiltered catalog rather than silently
    returning nothing.
    """
    warnings = validate_profile(user_prefs, songs)
    for warning in warnings:
        logger.warning("guardrail: %s", warning)

    negative_genres = user_prefs.get('negative_genres', [])
    filtered_songs = [song for song in songs if song['genre'] not in negative_genres]

    if not filtered_songs and songs:
        fallback_warning = (
            f"negative_genres {negative_genres} excluded every song in the catalog -- "
            "falling back to the unfiltered catalog so a recommendation can still be made"
        )
        logger.warning("guardrail: %s", fallback_warning)
        warnings.append(fallback_warning)
        filtered_songs = songs

    scored_songs = []
    for song in filtered_songs:
        score, reasons = score_song(user_prefs, song)

        # Create explanation string from reasons
        explanation = ", ".join([r.split("(")[0].strip() for r in reasons])

        scored_songs.append((song, score, explanation, reasons))

    ranked = sorted(scored_songs, key=lambda x: x[1], reverse=True)[:k]
    return RecommendationResult(items=ranked, warnings=warnings)
