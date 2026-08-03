# System Evaluation: Music Recommender Edge Cases

## Context
This project implements a music recommender system that scores songs based on a user preference profile and returns ranked recommendations. The scoring algorithm includes:

- Genre matching (+2.0 points)
- Mood matching (+1.5 points)
- Numerical feature scoring (energy, valence, danceability with tolerance bands)
- Acousticness bonus
- Hard filter for negative genres

## Relevant Files to Review
- `src/recommender.py` - Core implementation with `score_song()` and `recommend_songs()`
- `src/main.py` - CLI interface and output formatting
- `src/test_profiles.py` - Three baseline user profiles (High-Energy Pop, Chill Lofi, Deep Intense Rock)
- `data/songs.csv` - Song database (if available)

## Task: Generate Adversarial User Profiles

Please design **at least 5 adversarial or edge-case user preference profiles** that could:

1. **Expose conflicting preferences** - e.g., user wants energy 0.9 but mood "sad" (conflicting emotional signals)
2. **Test tolerance band edge cases** - e.g., user has extremely strict tolerance (0.05) vs. very loose tolerance (0.40)
3. **Create degenerate scenarios** - e.g., user who likes acoustic but dislikes all genres with high acousticness
4. **Test extreme values** - e.g., all feature weights set to 0, or one weight at 1.0
5. **Create preference loops** - e.g., user likes a genre but dislikes all moods associated with it
6. **Test empty/impossible constraints** - e.g., user avoids so many genres that few songs remain

## Questions to Answer

For each adversarial profile, please:

1. **Describe the scenario**: What makes this profile unusual or challenging?
2. **Predict the behavior**: How should the recommender ideally handle this?
3. **Identify potential bugs**: What could go wrong? What unexpected behavior might occur?
4. **Suggest fixes** (if applicable): How could the scoring algorithm be made more robust?

## Example Adversarial Profile Format

```python
CONFLICTING_EMOTIONS = {
    "profile_name": "Conflicting Emotions",
    "description": "User wants high-energy (0.9) but melancholic mood",
    "favorite_genre": "rock",
    "favorite_mood": "melancholic",  # Low valence
    "target_energy": 0.90,           # High energy
    "target_valence": 0.25,          # Low valence (sad)
    ...
}
```

---

## Please Generate and Analyze:

1. **Conflicting Emotional States** - Energy vs. Mood mismatch
2. **Extreme Tolerance Bands** - Very strict or very loose constraints
3. **Genre-Mood Paradox** - Liking a genre but rejecting its typical mood
4. **Weight Degeneration** - Extreme or zero feature weights
5. **Massive Negative Genre List** - User rejects most genres
6. Any other edge cases you think would break the system

For each, explain:
- Why it's a challenge
- What the current implementation does
- Whether that's acceptable or if it's a bug
- How the algorithm could be improved
