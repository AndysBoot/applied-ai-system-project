"""
Command line runner for the Music Recommender Simulation.

Loads the catalog, scores it against a user profile (through the guardrail
and smoothed-tolerance scoring in recommender.py), and prints ranked
recommendations with both a deterministic reason breakdown and a
RAG-generated natural language explanation (src/explain.py).
"""

import logging
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; ANTHROPIC_API_KEY can also be set directly in the environment

from src.recommender import load_songs, recommend_songs
from src.explain import generate_explanation

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    songs = load_songs("data/songs.csv")

    # Refined taste profile with tolerance bands and feature weights
    user_prefs = {
        # Core preferences
        "favorite_genre": "indie pop",
        "favorite_mood": "happy",
        "target_energy": 0.75,
        "target_valence": 0.8,
        "target_danceability": 0.75,

        # Tolerance bands (how much deviation is acceptable)
        "energy_tolerance": 0.15,          # accept 0.60–0.90
        "valence_tolerance": 0.15,         # accept 0.65–0.95 (valence is most important)
        "danceability_tolerance": 0.10,    # stricter tolerance here

        # Feature importance weights
        "feature_weights": {
            "valence": 0.30,               # happiness is PRIMARY
            "energy": 0.25,                # secondary
            "genre_match": 0.20,           # nice-to-have
            "danceability": 0.15,          # tertiary
            "acousticness": 0.10,          # bonus
        },

        # Additional constraints
        "likes_acoustic": True,            # prefer some acoustic elements
        "acoustic_preference_strength": 0.6,  # not required, but nice-to-have
        "negative_genres": ["metal"],      # explicitly avoid
    }

    if os.environ.get("ANTHROPIC_API_KEY"):
        logger.info("ANTHROPIC_API_KEY detected -- explanations will use the RAG/Claude path")
    else:
        logger.info("No ANTHROPIC_API_KEY set -- explanations will use the deterministic fallback")

    result = recommend_songs(user_prefs, songs, k=5)

    if result.warnings:
        print("\n" + "="*70)
        print("GUARDRAIL WARNINGS")
        print("="*70)
        for warning in result.warnings:
            print(f"  ! {warning}")

    print("\n" + "="*70)
    print("TOP 5 MUSIC RECOMMENDATIONS")
    print("="*70)

    for idx, rec in enumerate(result.items, 1):
        song, score, explanation, reasons = rec

        # Song header
        print(f"\n{idx}. {song['title']}")
        print(f"   Artist: {song['artist']} | Genre: {song['genre']} | Mood: {song['mood']}")

        # Score with visual bar (ASCII-only so it renders on any terminal encoding)
        bar_length = max(0, min(30, int(score / 12 * 30)))  # Scale to 30-char bar (max score ~12)
        bar = "#" * bar_length + "-" * (30 - bar_length)
        print(f"   Score: {score:.2f}/12.0 [{bar}]")

        # Detailed reasons (deterministic, always available)
        print(f"   Why matched:")
        for reason in reasons:
            print(f"     - {reason}")

        # AI explanation (RAG over the catalog when a key is configured, else
        # the same deterministic reasons rendered as prose)
        ai_explanation = generate_explanation(user_prefs, song, score, reasons, songs)
        print(f"   AI Explanation: {ai_explanation}")

        print("-" * 70)

    print()


if __name__ == "__main__":
    main()
