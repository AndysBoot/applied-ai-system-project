from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv
import os
from pathlib import Path

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
    tolerance = user_prefs.get('tolerance', 0.2)
    base_value = 8.0

    # Valence (happiness)
    target_valence = user_prefs.get('target_valence', 0.5)
    valence_diff = abs(song['valence'] - target_valence)
    if valence_diff <= tolerance:
        valence_score = feature_weights['valence'] * base_value
    else:
        valence_score = feature_weights['valence'] * base_value * 0.5
    score += valence_score
    reasons.append(f"valence within range (+{valence_score:.1f})")

    # Energy
    target_energy = user_prefs.get('target_energy', 0.5)
    energy_diff = abs(song['energy'] - target_energy)
    if energy_diff <= tolerance:
        energy_score = feature_weights['energy'] * base_value
    else:
        energy_score = feature_weights['energy'] * base_value * 0.5
    score += energy_score
    reasons.append(f"energy within range (+{energy_score:.1f})")

    # Danceability
    target_danceability = user_prefs.get('target_danceability', 0.5)
    danceability_diff = abs(song['danceability'] - target_danceability)
    if danceability_diff <= tolerance:
        danceability_score = feature_weights['danceability'] * base_value
    else:
        danceability_score = feature_weights['danceability'] * base_value * 0.5
    score += danceability_score
    reasons.append(f"danceability within range (+{danceability_score:.1f})")

    # Acousticness Bonus
    if user_prefs.get('likes_acoustic', False) and song['acousticness'] > 0.7:
        acoustic_score = user_prefs.get('acoustic_preference_strength', 1.0)
        score += acoustic_score
        reasons.append(f"acoustic bonus (+{acoustic_score:.1f})")

    return (score, reasons)

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str, List[str]]]:
    """Recommend top k songs ranked by score, filtering negative genres."""
    scored_songs = []

    for song in songs:
        # Filter out songs with negative genres (hard filter)
        if song['genre'] in user_prefs.get('negative_genres', []):
            continue

        score, reasons = score_song(user_prefs, song)

        # Create explanation string from reasons
        explanation = ", ".join([r.split("(")[0].strip() for r in reasons])

        scored_songs.append((song, score, explanation, reasons))

    # Return top k songs sorted by score (highest first)
    return sorted(scored_songs, key=lambda x: x[1], reverse=True)[:k]
