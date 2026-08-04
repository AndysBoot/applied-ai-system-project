# 🎧 Music Recommender: An Applied AI System

## Project Overview

**Original Project (Modules 1-3):** A rule-based music recommendation engine that scores songs from a catalog against user preferences (genre, mood, energy, valence, danceability) and returns ranked recommendations with justifications.

**Extended for Applied AI (Module 4):** The recommendation engine now includes a guardrail layer that checks for contradictions in user profiles before scoring, an automatically generated adversarial test suite of 8 profiles that stress-test the system, and a smart template-based explanation layer that provides natural language explanations for why songs were recommended—all without requiring API keys.

---

## What This Does and Why It Matters

Originally, the music recommendation app was simply based off fabricated data and suggestions. With this new project, we now recommend actual songs based off your various music choices, via the usage of the MusicBrainz API

This project demonstrates how to:
- **Design a transparent scoring algorithm** that's easy to reason about and debug
- **Validate inputs proactively** via an AI-powered guardrail layer that detects contradictions before scoring
- **Test systematically against adversarial cases** with an automated regression suite that stress-tests edge cases
- **Generate natural-language explanations** using smart template-based AI that grounds text in actual song data
- **Integrate reliability mechanisms seamlessly** so the core system remains testable and trustworthy

The result is a recommender that's honest about its limitations, includes two AI-powered reliability layers (guardrails and smart explanations), and ensures accuracy while providing users countless recommendations they would have previously never encountered.

---

## AI-Powered Reliability Features (Applied AI Extensions)

This project adds **two substantial AI features** to the base rule-based recommender:

### 1. **Guardrail Layer** — Pattern-Matching Reliability Mechanism
**File:** [src/guardrails.py](src/guardrails.py)

Detects contradictions and degenerate inputs *before* scoring runs:
- **Zero feature weights** — all numerical features disabled, ranking driven by genre/mood only
- **Conflicting emotions** — high energy + low valence (uncommon pairing)
- **Strict tolerance bands** — bands under 0.08 may filter out most catalog
- **Acoustic paradox** — user wants acoustic + very high energy (rare combination)
- **Genre wipeout** — negative_genres list excludes most/all catalog genres

Behavior: **warns without blocking** — preserves transparency and lets caller understand why results may be sparse or unusual.

### 2. **Smart Template-Based Explanations** — AI-Generated Natural Language
**File:** [src/explain.py](src/explain.py)

Generates natural-language explanations by:
1. **Pattern matching** — analyzes scoring breakdown to identify what matched (genre, mood, features)
2. **Attribute conversion** — converts numeric values to descriptive phrases (0.85 energy → "energetic")
3. **Template selection** — picks contextual templates based on which factors drove the recommendation
4. **Natural generation** — produces warm, concrete, data-grounded explanations

Example output: *"Monumentum hits the sweet spot with its energetic energy and highly danceable rhythm, perfect for your preferences."*

### 3. **Automated Adversarial Testing** — Evaluation Loop
**File:** [tests/test_adversarial.py](tests/test_adversarial.py)

Systematic testing against 8 edge-case profiles that stress-test the system:
- Perfectionist (strict tolerance bands)
- No features (all weights zero)
- Conflicting emotions (high energy + low valence)
- Energy obsessed (one feature dominates)
- Acoustic paradox (acoustic + very high energy)
- Genre-mood paradox (incompatible preferences)
- Picky eater (many negative genres)
- Indifferent (very loose tolerances)

**All 21 tests pass**, validating that the system never crashes, produces bounded scores, fires expected guardrail warnings, and returns k results even for degenerate inputs.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  User Profile + Song Catalog                                 │
│  (favorite_genre, mood, energy/valence/dance targets, etc.) │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
         ┌─────────────────────────────┐
         │ GUARDRAIL LAYER             │
         │ (src/guardrails.py)         │
         │ Validate profile for:       │
         │ • Zero weights              │
         │ • Strict tolerance bands    │
         │ • Energy-mood conflicts     │
         │ • Genre filter wipeout      │
         └──────────┬──────────────────┘
                    ↓ (warnings logged, never blocks)
      ┌─────────────────────────────────┐
      │ RECOMMENDATION ENGINE           │
      │ (src/recommender.py)            │
      │ • Load songs from SQLite DB     │
      │ • Score with smoothed tolerance │
      │ • Rank, filter, fallback        │
      └──────────┬──────────────────────┘
                 ↓
      ┌─────────────────────────────────┐
      │ SMART EXPLANATION LAYER         │
      │ (src/explain.py)                │
      │ Analyze scoring pattern +       │
      │ select template grounded in     │
      │ the song's own data             │
      └──────────┬──────────────────────┘
                 ↓
         ┌──────────────────────────────┐
         │ OUTPUT: Ranked songs + scores │
         │ + reasons + warnings          │
         └──────────────────────────────┘
```

The system uses:
- **SQLite database** (`data/songs.db`) populated from the MusicBrainz API with real songs(there are currently 2,000 songs approximately) (title, artist, genre; mood/energy/valence estimated per genre)
- **Guardrail checks** that warn about contradictions *before* scoring (all feature weights zero, high energy + low valence, overly strict tolerance, etc.)
- **Automated adversarial test suite** with 8 edge-case profiles that run on every `pytest` to catch regressions

See [system_diagram.md](system_diagram.md) for a detailed flowchart.

---

## Setup Instructions

### Prerequisites
- **Python 3.9+**
- **pip**
- **SQLite3** (usually pre-installed)

### 1. Clone and Install Dependencies

```bash
cd applied-ai-system-project
pip install -r requirements.txt
```

### 2. Populate the Song Catalog

The system uses `data/songs.db` (SQLite). You can populate it with real songs from MusicBrainz:

```bash
# Import songs from a genre (e.g., rock, indie pop, jazz)
python scripts/manage_songs.py import-musicbrainz rock --limit 50

# Or manually add songs
python scripts/manage_songs.py add "Song Title" "Artist Name" genre mood energy tempo_bpm valence danceability acousticness
```

For testing without live data, the test suite falls back to `data/songs.csv` (a small fabricated 17-song catalog).

### 3. Run the CLI

```bash
python src/main.py
```

This loads the catalog and recommends 5 songs for a built-in user profile (indie pop, happy mood, high energy). Output includes:
- Ranked songs with scores
- Reason breakdown (genre/mood/feature matches)
- Guardrail warnings (if any contradictions detected)
- Smart template-based explanation explaining why each song was recommended

### 4. Run the Web UI

```bash
streamlit run app.py
```

Opens an interactive web interface where you can:
- Select favorite genre and mood
- Set energy/valence/danceability targets and tolerance bands
- Adjust feature weights
- See recommendations with smart AI-generated explanations and guardrail warnings in real-time

### 5. Run Tests

```bash
pytest
```

Runs:
- `tests/test_recommender.py` — baseline profiles (high-energy pop, chill lofi, deep rock)
- `tests/test_adversarial.py` — all 8 adversarial profiles (edge cases)

All 8 adversarial profiles are exercised on every run to catch regressions.

---

## Sample Interactions

### Example 1: High-Energy Pop Enthusiast
**Input Profile:**
```python
{
    "favorite_genre": "pop",
    "favorite_mood": "happy",
    "target_energy": 0.85,
    "target_valence": 0.85,
    "target_danceability": 0.80,
    "energy_tolerance": 0.10,
    "feature_weights": {"valence": 0.30, "energy": 0.25, "danceability": 0.15, ...}
}
```

**Output (top 3):**
```
1. Sunny Beats (pop, happy)
   Score: 8.2
   Reasons: genre match (+2.0), mood match (+1.5), valence within range (+1.8), 
            energy within range (+1.6), danceability within range (+1.3)
   Explanation: "Sunny Beats is a perfect match for your upbeat taste—it's a high-energy 
                pop track with joyful vibes and a danceable rhythm."

2. Dance All Night (pop, energetic)
   Score: 7.9
   Reasons: genre match (+2.0), valence within range (+1.6), energy within range (+1.5), ...

3. Uplifting Vibes (pop, happy)
   Score: 7.5
   Reasons: genre match (+2.0), mood match (+1.5), valence within range (+1.5), ...
```

### Example 2: Perfectionist with Strict Tolerance (Edge Case)
**Input Profile:**
```python
{
    "favorite_genre": "indie",
    "favorite_mood": "happy",
    "target_energy": 0.60,
    "target_valence": 0.70,
    "energy_tolerance": 0.05,       # Very strict!
    "valence_tolerance": 0.05,      # Very strict!
    "danceability_tolerance": 0.05, # Very strict!
}
```

**Guardrail Warnings:**
```
! energy_tolerance is very strict (0.05) — may return fewer than requested recommendations
! valence_tolerance is very strict (0.05) — may return fewer than requested recommendations
! danceability_tolerance is very strict (0.05) — may return fewer than requested recommendations
```

**Output (still returns 5, but from a smaller filtered pool):**
The system gracefully handles the strict constraints by using smoothed tolerance scoring 
rather than hard cliffs. Even with 0.05 tolerance, it finds 5 songs instead of failing.

### Example 3: Conflicting Emotions (Edge Case)
**Input Profile:**
```python
{
    "favorite_genre": "rock",
    "favorite_mood": "melancholic",
    "target_energy": 0.90,      # High energy
    "target_valence": 0.20,     # Low valence (sad)
    "target_danceability": 0.35,
}
```

**Guardrail Warning:**
```
! high target_energy (0.90) combined with low target_valence (0.20) is an uncommon 
  emotional combination — few songs in a typical catalog pair high energy with low happiness
```

**Output:**
```
1. Storm Runner (rock, intense)
   Score: 6.8
   Reasons: genre match (+2.0), energy within range (+2.1), valence within range (+1.2), ...
   Explanation: "Storm Runner delivers intense, high-energy rock with emotional depth—
                the kind of driving intensity that captures melancholy without softness."
```

The guardrail warns that this is unusual, but the system still finds a sensible match if one exists in the catalog.

---

## Design Decisions

### 1. **Guardrail Layer: Warn, Don't Block**
We deliberately chose warnings over auto-correction. If a profile has all feature weights set to zero, we could silently reset them to defaults—but that hides what the system is actually doing. Instead, we warn the user and still produce a recommendation (driven by genre/mood bonuses). This makes behavior transparent and predictable.

**Trade-off:** Users see warnings they may not expect, but they understand why the ranking looks the way it does.

### 2. **Smoothed Tolerance Scoring Instead of Hard Cliffs**
The original design scored songs fully within the tolerance band, then instantly dropped to half points beyond it—a sharp cliff that caused rankings to swing wildly for tiny changes. We switched to linear decay: score stays full within the band, then gradually decays from the tolerance boundary to a floor at twice the tolerance. This fixes the "cliff" without changing the scoring at the boundary itself.

**Trade-off:** Slightly more computation (linear interpolation), but much more stable rankings and better behavior at edge cases.

### 3. **Fallback for Genre Filter Wipeout**
If a user's `negative_genres` list would exclude every song in the catalog, we fall back to the unfiltered catalog instead of returning zero results. This is rare but catastrophic if not handled.

**Trade-off:** Users might see songs they marked as "avoid," but they get recommendations instead of an empty result.

### 4. **Smart Template-Based Explanations**
We generate explanations by analyzing the scoring patterns and song attributes, then selecting and filling contextual templates. The system identifies what factors matched (genre, mood, energy, etc.) and crafts natural-sounding explanations without any external API calls.

**Trade-off:** Template-based explanations are deterministic and fast with no API keys or privacy concerns, but require careful template design to feel natural. The approach is fully transparent about why songs were recommended.

### 5. **Database-Only Loading for Live App**
The live app (`src/main.py`, `app.py`) loads exclusively from SQLite (`data/songs.db`), not the fabricated CSV. If the database is empty, it errors with instructions on how to populate it, instead of silently falling back to toy data. This prevents confusion between real and example catalogs.

**Trade-off:** Users must explicitly populate the database, but we avoid the silent data mismatch that happens when a tool unexpectedly switches to toy data.

---

## Testing Summary

### Baseline Profiles (in `src/test_profiles.py`)
- **High-Energy Pop Enthusiast:** Upbeat, danceable, happy (typical case)
- **Chill Lofi Relaxation:** Low energy, acoustic, calm (different energy range)
- **Deep Intense Rock:** High energy but melancholic (emotional complexity)

### Adversarial Profiles (in `src/adversarial_profiles.py`)
Eight edge-case profiles designed to expose algorithm weaknesses:

1. **Conflicting Emotions:** High energy (0.90) + low valence (0.20) — uncommon combo
2. **Perfectionist:** Extreme tolerance bands (0.05) — may filter out most songs
3. **Indifferent:** Loose tolerance (0.40) — almost all songs match, ranking becomes arbitrary
4. **Genre-Mood Paradox:** Likes jazz but wants electronic sound — conflicting signals
5. **Energy Obsessed:** One feature weight dominates (energy=1.0, others=0) — degeneracy
6. **Picky Eater:** 12 genres in negative list — may empty the catalog
7. **Acoustic Paradox:** Likes acoustic but wants very high energy (0.95) — contradictory
8. **No Features:** All feature weights zero (0.0) — ranking driven by genre/mood only

### What Tests Verify
- ✅ No profile crashes the system or produces non-finite scores
- ✅ Perfectionist tolerance still returns 5 results despite 0.05 bands
- ✅ Zero-weight profile triggers "zero features" guardrail warning
- ✅ Conflicting emotions trigger "high energy + low valence" warning
- ✅ Acoustic paradox triggers the acoustic/energy warning
- ✅ Genre filter wipeout falls back to unfiltered catalog

**Test Results:** All tests pass. Adversarial profiles run on every `pytest` as a regression suite, ensuring the system remains robust even after code changes.

### What We Learned
- **Hard cliffs are dangerous.** The original hard-cliff tolerance scoring was stable for "typical" cases but produced wild ranking swings for edge cases just outside the band. Smoothed decay fixed this without breaking existing behavior.
- **Dead config is invisible.** The scoring code was reading a generic `tolerance` key that no profile ever set, instead of per-feature `energy_tolerance`/`valence_tolerance` keys. This silent no-op went unnoticed for months. A good reminder to audit configuration reading.
- **Degenerate inputs still produce outputs.** When all feature weights are zero, the system doesn't crash—it just returns rankings driven purely by genre/mood. That's technically correct but probably not useful. A guardrail warning helps the user understand what's happening.
- **Testing requires adversarial thinking.** The baseline profiles all worked fine, but the adversarial suite caught real bugs (tolerance fallback, genre filter wipeout, cliff behavior). Thinking like an attacker matters.

---

## Reflection

This project was a deep dive into **building AI systems that are trustworthy, not just functional.** 

The biggest insight was realizing that "working" isn't the same as "robust." The original recommendation engine produced sensible results for typical users, but the moment you fed it edge cases—contradictory preferences, extreme tolerance bands, degenerate weights—the behavior became hard to reason about or sometimes just wrong. 

What changed everything was adding three layers on top of the core scoring:
1. **Guardrails** that *explain* why a profile is tricky (without blocking the user)
2. **Automated testing** against adversarial cases that become regression suite
3. **Grounded explanations** that cite actual data instead of inventing reasons

This mirrors how ML systems should evolve: you build something that works, then you invest in making it *understandable and resilient*. That's where the complexity actually lives.

The system taught me that **constraints are your friend**. The smoothed tolerance curve, the fallback mechanism for empty catalogs, the guardrail layer that warns instead of auto-correcting—all of these feel like overhead until you hit the edge case and realize they save your system from silent failures.

See [model_card.md](model_card.md) for the full responsible-AI reflection (AI collaboration examples, helpful vs. flawed suggestions, system limitations).

---

## Running the Project

**Quick Start:**
```bash
# Install
pip install -r requirements.txt

# Populate database (optional—tests use CSV fallback)
python scripts/manage_songs.py import-musicbrainz rock --limit 25

# Run CLI
python src/main.py

# Run tests
pytest

# Run web UI
streamlit run app.py
```

**Note:** Explanations are generated using smart templates that analyze your preferences and song attributes—no API keys or external services needed.

---

## Project Structure

```
.
├── src/
│   ├── recommender.py          # Core scoring + ranking logic
│   ├── guardrails.py           # Profile validation
│   ├── explain.py              # Smart template-based explanations
│   ├── main.py                 # CLI runner
│   ├── test_profiles.py        # 3 baseline user profiles
│   ├── adversarial_profiles.py # 8 edge-case profiles
│   ├── db.py                   # SQLite helper
│   └── musicbrainz.py          # MusicBrainz API integration
├── tests/
│   ├── test_recommender.py     # Baseline profile checks
│   └── test_adversarial.py     # Adversarial regression suite
├── scripts/
│   └── manage_songs.py         # Database seeding CLI
├── data/
│   ├── songs.db                # Live catalog (SQLite)
│   └── songs.csv               # Fabricated example (tests only)
├── app.py                      # Streamlit web UI
├── model_card.md               # Full system documentation + responsible-AI reflection
├── system_diagram.md           # Architecture flowchart
└── README.md                   # This file
```

---

## Next Steps / Future Work

1. **Make acoustic a learnable feature**, not a flat bonus
2. **Extend guardrails** to detect genre/mood pairings rare in the actual catalog (currently uses hand-picked thresholds)
3. **Verify template explanations** automatically stay grounded (check output only references attributes present in the song's own data)
4. **Investigate catalog bias** (currently 35% low-energy, 30% high-energy; may skew recommendations)

---

## Credits

Built as part of the AI 110 Applied AI Systems course at Codepath.org. The project demonstrates how to move from a simple rule-based system to a production-like system with guardrails, systematic testing, and responsible-AI practices.

See [model_card.md](model_card.md) for detailed reflection on AI collaboration and system design trade-offs.
