"""
User preference profiles for testing the music recommender system.
These represent distinct listener archetypes with different tastes.
"""

# Profile 1: High-Energy Pop Enthusiast
# Loves upbeat, danceable pop music with positive vibes
HIGH_ENERGY_POP = {
    "profile_name": "High-Energy Pop Enthusiast",
    "favorite_genre": "pop",
    "favorite_mood": "happy",
    "target_energy": 0.85,
    "target_valence": 0.85,
    "target_danceability": 0.80,

    "energy_tolerance": 0.10,
    "valence_tolerance": 0.10,
    "danceability_tolerance": 0.10,

    "feature_weights": {
        "valence": 0.30,
        "energy": 0.25,
        "genre_match": 0.20,
        "danceability": 0.15,
        "acousticness": 0.10,
    },

    "likes_acoustic": False,
    "acoustic_preference_strength": 0.0,
    "negative_genres": ["metal", "experimental"],
}

# Profile 2: Chill Lofi Relaxation
# Prefers ambient, acoustic, low-energy music for studying/relaxing
CHILL_LOFI = {
    "profile_name": "Chill Lofi Relaxation",
    "favorite_genre": "lofi",
    "favorite_mood": "calm",
    "target_energy": 0.30,
    "target_valence": 0.55,
    "target_danceability": 0.20,

    "energy_tolerance": 0.15,
    "valence_tolerance": 0.20,
    "danceability_tolerance": 0.15,

    "feature_weights": {
        "valence": 0.25,
        "energy": 0.20,
        "genre_match": 0.20,
        "danceability": 0.10,
        "acousticness": 0.25,
    },

    "likes_acoustic": True,
    "acoustic_preference_strength": 1.5,
    "negative_genres": ["metal", "screamo", "hardcore"],
}

# Profile 3: Deep Intense Rock
# Seeks complex, high-energy rock with emotional depth (not happy, but intense)
DEEP_INTENSE_ROCK = {
    "profile_name": "Deep Intense Rock",
    "favorite_genre": "rock",
    "favorite_mood": "melancholic",
    "target_energy": 0.75,
    "target_valence": 0.35,
    "target_danceability": 0.40,

    "energy_tolerance": 0.15,
    "valence_tolerance": 0.15,
    "danceability_tolerance": 0.15,

    "feature_weights": {
        "valence": 0.30,
        "energy": 0.30,
        "genre_match": 0.20,
        "danceability": 0.10,
        "acousticness": 0.10,
    },

    "likes_acoustic": False,
    "acoustic_preference_strength": 0.0,
    "negative_genres": ["pop", "bubblegum pop", "dance"],
}

# All profiles for easy iteration
ALL_PROFILES = [
    HIGH_ENERGY_POP,
    CHILL_LOFI,
    DEEP_INTENSE_ROCK,
]

if __name__ == "__main__":
    for profile in ALL_PROFILES:
        print(f"\n{profile['profile_name']}")
        print(f"  Genre: {profile['favorite_genre']}, Mood: {profile['favorite_mood']}")
        print(f"  Energy: {profile['target_energy']}, Valence: {profile['target_valence']}, Danceability: {profile['target_danceability']}")
        print(f"  Avoids: {', '.join(profile['negative_genres'])}")
