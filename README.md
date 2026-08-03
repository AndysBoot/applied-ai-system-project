# 🎵 Music Recommender — Applied AI System

## Project Summary

A small music recommender that scores a 17-song catalog against a user taste profile
(favorite genre/mood, target energy/valence/danceability, tolerance bands, feature weights)
and returns ranked recommendations. It started as a Module 3 rule-based scoring exercise;
this version extends it with two AI features that are fully integrated into the main
pipeline rather than bolted on as side scripts:

- **A guardrail/reliability layer** (`src/guardrails.py`) that validates a profile before
  scoring — flagging contradictory or degenerate input (zero feature weights, overly strict
  tolerance, conflicting energy/mood targets, the acoustic/high-energy paradox, negative-genre
  lists that would wipe out the catalog) — and an automated test suite
  (`tests/test_adversarial.py`) that runs all 8 adversarial profiles through the real pipeline
  on every `pytest` run.
- **A RAG explanation layer** (`src/explain.py`) that retrieves a recommended song's full
  attributes plus a few catalog songs sharing its genre/mood, and asks Claude to write a short
  explanation grounded only in that retrieved data — falling back to the original deterministic
  reason string whenever no API key is configured or the call fails.

See [`system_diagram.md`](system_diagram.md) for the full component/data-flow diagram.

---

## How The System Works

Each song has: `id`, `title`, `artist`, `genre`, `mood`, `energy`, `tempo_bpm`, `valence`,
`danceability`, `acousticness` (`data/songs.csv`).

Each user profile has: `favorite_genre`, `favorite_mood`, target values for `energy`/`valence`/
`danceability`, a tolerance band per feature, per-feature `feature_weights`, an optional
`likes_acoustic` preference, and a `negative_genres` exclusion list.

### Scoring (`src/recommender.py`)

1. **Genre match**: +2.0 if the song's genre equals the profile's favorite genre.
2. **Mood match**: +1.5 if the song's mood equals the profile's favorite mood.
3. **Numerical features** (energy, valence, danceability): each scores `weight × 8.0` at zero
   deviation from the target, holds full score through the tolerance band, then **decays
   linearly** down to half score by the time the deviation reaches twice the tolerance, and
   floors there. (Earlier versions of this project scored numerical features with a hard cliff —
   full score inside the tolerance band, an instant drop to half score the moment it was
   exceeded. That's now smoothed, per the fix documented in `model_card.md`.)
4. **Acoustic bonus**: if `likes_acoustic` is true and the song's acousticness is above 0.7, add
   `acoustic_preference_strength`.
5. **Hard filter**: songs whose genre is in `negative_genres` are excluded — *unless* that filter
   would exclude the entire catalog, in which case the system falls back to the unfiltered
   catalog (logged as a guardrail warning) rather than silently returning nothing.

### Guardrails (`src/guardrails.py`)

Before scoring, `validate_profile()` checks the profile itself and returns warnings (it never
blocks a recommendation — a "bad" profile still gets scored, just with visible caveats):

- all numerical feature weights are zero
- high target energy combined with low target valence (an uncommon emotional combination)
- any tolerance band under 0.08 (may return fewer results than requested from a small catalog)
- `likes_acoustic=True` combined with a very high target energy (acoustic songs are typically
  low-energy)
- a `negative_genres` list covering most of the genres actually present in the catalog

These checks come directly from the 8 adversarial profiles in `src/adversarial_profiles.py` and
the bugs documented in `model_card.md`, and `tests/test_adversarial.py` asserts they fire for the
profiles that should trigger them.

### RAG Explanations (`src/explain.py`)

For each recommended song, `generate_explanation()`:

1. **Retrieves** the song's full attribute row plus up to 3 other catalog songs sharing its
   genre or mood.
2. **Generates** a 1–2 sentence explanation with Claude, prompted to use *only* that retrieved
   data — it's explicitly told not to invent attributes, artists, or claims.
3. **Falls back** to the deterministic reason string (e.g. `"genre match, mood match, valence
   within range"`) if `ANTHROPIC_API_KEY` isn't set, the `anthropic` package isn't installed, or
   the API call fails for any reason. This function always returns a usable string — callers
   never need to check whether the AI call actually happened.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Enable live RAG explanations by copying `.env.example` to `.env` and filling in
   your own key:

   ```bash
   cp .env.example .env
   # then edit .env and set ANTHROPIC_API_KEY=sk-...
   ```

   This step is entirely optional — the app runs correctly with no key configured, using the
   deterministic explanation instead. There is no free tier for the Claude API, but usage here
   is a handful of short calls per run and costs a small fraction of a cent each.

### Running the CLI

```bash
python -m src.main
```

### Running the Streamlit app

```bash
streamlit run app.py
```

Lets you set your taste profile with sliders/selects (populated from the actual catalog) instead
of editing the hardcoded profile in `main.py`, and includes a session-only password field to try
a Claude API key without setting up `.env` at all.

### Running Tests

```bash
python -m pytest
```

This runs the baseline profile tests (`tests/test_recommender.py`) and the full adversarial
regression suite (`tests/test_adversarial.py`), which exercises all 8 edge-case profiles from
`src/adversarial_profiles.py` against the real pipeline — 16 tests total.

---

## Sample Recommendation Output

```
======================================================================
TOP 5 MUSIC RECOMMENDATIONS
======================================================================

1. Rooftop Lights
   Artist: Indigo Parade | Genre: indie pop | Mood: happy
   Score: 9.10/12.0 [######################--------]
   Why matched:
     - genre match (+2.0)
     - mood match (+1.5)
     - valence within range (+2.4)
     - energy within range (+2.0)
     - danceability within range (+1.2)
   AI Explanation: genre match, mood match, valence within range, energy within range, danceability within range
----------------------------------------------------------------------

2. Sunrise City
   Artist: Neon Echo | Genre: pop | Mood: happy
   Score: 7.10/12.0 [#################-------------]
   Why matched:
     - mood match (+1.5)
     - valence within range (+2.4)
     - energy within range (+2.0)
     - danceability within range (+1.2)
   AI Explanation: mood match, valence within range, energy within range, danceability within range
----------------------------------------------------------------------
```

(Truncated — `python -m src.main` prints the full top 5. The "AI Explanation" line above is the
deterministic fallback, since no API key is set in this example; with a key configured it reads
as natural-language prose instead.)

---

## Experiments You Tried

- Removing the smoothing and reverting to a hard tolerance cliff makes the `PERFECTIONIST`
  profile's rankings swing sharply between songs just inside vs. just outside the 0.05 band —
  the smoothed version produces a much more gradual ranking.
- Discovered that `score_song` was reading a generic `tolerance` key that no profile actually
  sets (every profile sets `energy_tolerance`/`valence_tolerance`/`danceability_tolerance`
  instead) — every profile's per-feature tolerance had silently been a no-op. Fixing that changed
  the default profile's top-5 ranking (see `model_card.md`).
- Setting all `feature_weights` to zero (`NO_FEATURES` / `ENERGY_OBSESSED` profiles) confirms the
  guardrail warning fires and the ranking collapses to genre/mood match only, as expected.

---

## Limitations and Risks

- Tiny catalog (17 songs) — recommendations are only as good as what's in `data/songs.csv`, and
  strict profiles can exhaust the meaningfully-different options quickly.
- No understanding of lyrics, language, or actual audio — everything is numeric metadata.
- The catalog's genre/energy distribution isn't balanced, so genres that are underrepresented (or
  paired with atypical energy/mood combinations) are structurally harder to satisfy — see
  `model_card.md` for specifics.
- The RAG explanation is grounded in retrieved data and instructed not to invent facts, but it is
  still an LLM generation step — treat it as a nicer-sounding restatement of the deterministic
  reasons, not an independent judgment.

See [`model_card.md`](model_card.md) for the full evaluation history.

---

## Reflection

Read [`model_card.md`](model_card.md) for the full write-up of what the adversarial testing
surfaced, what was fixed, and what's left as future work.

Building the guardrail layer made it clear how much of "recommender quality" is really about
handling the profiles a system *shouldn't* have to handle gracefully — a contradictory or
degenerate preference shouldn't crash anything or silently produce nonsense, it should say so.
Wiring in the RAG explanation layer showed the flip side of that lesson: a generative layer needs
the same discipline, which is why it's restricted to only the data actually retrieved for that
song rather than left free to describe the music however it likes.
