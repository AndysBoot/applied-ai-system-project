"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


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

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\n" + "="*70)
    print("TOP 5 MUSIC RECOMMENDATIONS")
    print("="*70)

    for idx, rec in enumerate(recommendations, 1):
        song, score, explanation, reasons = rec

        # Song header
        print(f"\n{idx}. {song['title']}")
        print(f"   Artist: {song['artist']} | Genre: {song['genre']} | Mood: {song['mood']}")

        # Score with visual bar
        bar_length = int(score / 12 * 30)  # Scale to 30-char bar (max score ~12)
        bar = "█" * bar_length + "░" * (30 - bar_length)
        print(f"   Score: {score:.2f}/12.0 [{bar}]")

        # Detailed reasons
        print(f"   Why matched:")
        for reason in reasons:
            print(f"     • {reason}")

        print("-" * 70)

    print()


if __name__ == "__main__":
    main()
