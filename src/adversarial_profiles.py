"""
Adversarial and edge-case user preference profiles designed to test
the robustness of the music recommender scoring system.

Each profile is designed to expose potential weaknesses or unexpected
behaviors in the algorithm.
"""

# Edge Case 1: Conflicting Emotional States
# User wants high-energy music but sad emotional tone
# Potential issue: High energy is typically associated with happy/upbeat moods
CONFLICTING_EMOTIONS = {
    "profile_name": "Conflicting Emotions - High Energy Melancholy",
    "description": "High energy (0.90) but melancholic mood - uncommon combo",
    "favorite_genre": "rock",
    "favorite_mood": "melancholic",
    "target_energy": 0.90,          # High energy
    "target_valence": 0.20,          # Low valence (sad)
    "target_danceability": 0.35,

    "energy_tolerance": 0.10,
    "valence_tolerance": 0.10,
    "danceability_tolerance": 0.10,

    "feature_weights": {
        "valence": 0.30,
        "energy": 0.30,
        "genre_match": 0.20,
        "danceability": 0.10,
        "acousticness": 0.10,
    },

    "likes_acoustic": False,
    "acoustic_preference_strength": 0.0,
    "negative_genres": ["pop"],
}

# Edge Case 2: Extremely Strict Tolerance Bands
# User has very narrow acceptable ranges (0.05 tolerance)
# Potential issue: May reject most songs, return limited results
PERFECTIONIST = {
    "profile_name": "Perfectionist - Strict Tolerance",
    "description": "Extreme tolerance bands (0.05) - few songs will match",
    "favorite_genre": "indie",
    "favorite_mood": "happy",
    "target_energy": 0.60,
    "target_valence": 0.70,
    "target_danceability": 0.65,

    "energy_tolerance": 0.05,        # Very strict
    "valence_tolerance": 0.05,       # Very strict
    "danceability_tolerance": 0.05,  # Very strict

    "feature_weights": {
        "valence": 0.30,
        "energy": 0.25,
        "genre_match": 0.20,
        "danceability": 0.15,
        "acousticness": 0.10,
    },

    "likes_acoustic": True,
    "acoustic_preference_strength": 1.0,
    "negative_genres": ["metal"],
}

# Edge Case 3: Very Loose Tolerance Bands
# User accepts nearly everything (0.40+ tolerance)
# Potential issue: All songs score similarly, ranking may be arbitrary
INDIFFERENT = {
    "profile_name": "Indifferent - Loose Tolerance",
    "description": "Very wide tolerance (0.40) - almost all songs match",
    "favorite_genre": "electronic",
    "favorite_mood": "energetic",
    "target_energy": 0.50,
    "target_valence": 0.50,
    "target_danceability": 0.50,

    "energy_tolerance": 0.40,        # Very loose
    "valence_tolerance": 0.40,       # Very loose
    "danceability_tolerance": 0.40,  # Very loose

    "feature_weights": {
        "valence": 0.20,
        "energy": 0.20,
        "genre_match": 0.20,
        "danceability": 0.20,
        "acousticness": 0.20,
    },

    "likes_acoustic": False,
    "acoustic_preference_strength": 0.0,
    "negative_genres": [],  # No negative genres
}

# Edge Case 4: Genre-Mood Mismatch
# User likes jazz (typically smooth, acoustic) but wants intense, electronic sound
# Potential issue: Conflicting feature expectations
GENRE_MOOD_PARADOX = {
    "profile_name": "Genre-Mood Paradox",
    "description": "Likes jazz but wants high-energy electronic sound",
    "favorite_genre": "jazz",
    "favorite_mood": "energetic",
    "target_energy": 0.85,
    "target_valence": 0.75,
    "target_danceability": 0.70,

    "energy_tolerance": 0.10,
    "valence_tolerance": 0.10,
    "danceability_tolerance": 0.10,

    "feature_weights": {
        "valence": 0.30,
        "energy": 0.30,
        "genre_match": 0.20,
        "danceability": 0.15,
        "acousticness": 0.05,  # Low weighting
    },

    "likes_acoustic": False,  # Contradicts typical jazz
    "acoustic_preference_strength": 0.0,
    "negative_genres": ["electronic", "techno"],
}

# Edge Case 5: Degenerate Feature Weights
# One feature dominates (energy weight = 1.0), others = 0
# Potential issue: Valence and mood become irrelevant
ENERGY_OBSESSED = {
    "profile_name": "Energy Obsessed",
    "description": "Energy is everything (weight 1.0), others ignored",
    "favorite_genre": "pop",
    "favorite_mood": "happy",
    "target_energy": 0.95,
    "target_valence": 0.50,
    "target_danceability": 0.50,

    "energy_tolerance": 0.05,
    "valence_tolerance": 0.50,
    "danceability_tolerance": 0.50,

    "feature_weights": {
        "valence": 0.0,              # Irrelevant
        "energy": 1.0,               # Everything
        "genre_match": 0.0,
        "danceability": 0.0,
        "acousticness": 0.0,
    },

    "likes_acoustic": False,
    "acoustic_preference_strength": 0.0,
    "negative_genres": [],
}

# Edge Case 6: Massive Negative Genre List
# User rejects most genres, few songs remain
# Potential issue: May return < k songs, or ranking is based on tiny pool
PICKY_EATER = {
    "profile_name": "Picky Eater - Massive Negative Genre List",
    "description": "Rejects 10+ genres, may have very few options",
    "favorite_genre": "indie",
    "favorite_mood": "happy",
    "target_energy": 0.60,
    "target_valence": 0.75,
    "target_danceability": 0.50,

    "energy_tolerance": 0.15,
    "valence_tolerance": 0.15,
    "danceability_tolerance": 0.15,

    "feature_weights": {
        "valence": 0.30,
        "energy": 0.25,
        "genre_match": 0.20,
        "danceability": 0.15,
        "acousticness": 0.10,
    },

    "likes_acoustic": True,
    "acoustic_preference_strength": 0.5,
    "negative_genres": [
        "metal", "hardrock", "screamo", "pop", "mainstream",
        "electronic", "dubstep", "hiphop", "country", "reggae",
        "classical", "opera"
    ],
}

# Edge Case 7: Acoustic Paradox
# User loves acoustic (likes_acoustic=True) but targets very high-energy
# Potential issue: Acoustic music is typically low-energy; conflicting signals
ACOUSTIC_PARADOX = {
    "profile_name": "Acoustic Paradox",
    "description": "Likes acoustic music but wants high-energy electronic feel",
    "favorite_genre": "folk",
    "favorite_mood": "happy",
    "target_energy": 0.95,
    "target_valence": 0.85,
    "target_danceability": 0.80,

    "energy_tolerance": 0.10,
    "valence_tolerance": 0.10,
    "danceability_tolerance": 0.10,

    "feature_weights": {
        "valence": 0.30,
        "energy": 0.30,
        "genre_match": 0.20,
        "danceability": 0.15,
        "acousticness": 0.05,
    },

    "likes_acoustic": True,
    "acoustic_preference_strength": 2.0,  # High bonus
    "negative_genres": [],
}

# Edge Case 8: All Zeros
# Feature weights all zero - no real scoring happens
# Potential issue: All songs score 0 or nearly same (genre/mood bonus only)
NO_FEATURES = {
    "profile_name": "No Features - All Weights Zero",
    "description": "All feature weights are zero, only genre/mood matter",
    "favorite_genre": "indie pop",
    "favorite_mood": "happy",
    "target_energy": 0.50,
    "target_valence": 0.50,
    "target_danceability": 0.50,

    "energy_tolerance": 0.20,
    "valence_tolerance": 0.20,
    "danceability_tolerance": 0.20,

    "feature_weights": {
        "valence": 0.0,
        "energy": 0.0,
        "genre_match": 0.0,
        "danceability": 0.0,
        "acousticness": 0.0,
    },

    "likes_acoustic": False,
    "acoustic_preference_strength": 0.0,
    "negative_genres": [],
}

# All adversarial profiles for iteration
ALL_ADVERSARIAL_PROFILES = [
    CONFLICTING_EMOTIONS,
    PERFECTIONIST,
    INDIFFERENT,
    GENRE_MOOD_PARADOX,
    ENERGY_OBSESSED,
    PICKY_EATER,
    ACOUSTIC_PARADOX,
    NO_FEATURES,
]

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ADVERSARIAL USER PROFILES - EDGE CASE ANALYSIS")
    print("="*70)

    for profile in ALL_ADVERSARIAL_PROFILES:
        print(f"\n{profile['profile_name']}")
        print(f"Description: {profile['description']}")
        print(f"  Genre: {profile['favorite_genre']}, Mood: {profile['favorite_mood']}")
        print(f"  Energy: {profile['target_energy']}, Valence: {profile['target_valence']}, Dance: {profile['target_danceability']}")
        print(f"  Negative genres: {profile['negative_genres']}")
