# 🎵 Music Recommender — Applied AI System

## Project Summary

A small music recommender that scores a song catalog against a user taste profile
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

Each song has: `id`, `title`, `artist`, `genre`, `mood`, `energy`, `valence`,
`danceability`, `acousticness`. The live app loads these from `data/songs.db` (SQLite),
populated with real songs pulled from the MusicBrainz API -- see
[Populating the catalog](#populating-the-catalog) below. `data/songs.csv` is a small fabricated
example catalog kept only as a fixture for `tests/`; the app no longer reads it.

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

### Populating the catalog

The app reads its catalog exclusively from `data/songs.db` (SQLite) and will refuse to run
with instructions instead of silently substituting fake data if that database is empty. Populate
it with real songs from the [MusicBrainz API](https://musicbrainz.org/) (free, no API key needed):

```bash
python scripts/manage_songs.py import-musicbrainz rock --limit 25
python scripts/manage_songs.py import-musicbrainz pop --limit 25
python scripts/manage_songs.py list
```

Or bulk-import across all 27 genres at once:

```bash
python scripts/manage_songs.py import-musicbrainz-bulk --per-genre 100
```

Run single-genre import with any tag in `src/musicbrainz.py`'s `GENRE_FEATURE_ESTIMATES` to
add more. You can also add a single song by hand (`manage_songs.py add ...`) or bulk-import from
another CSV with the same columns as `data/songs.csv` (`manage_songs.py import-csv <path>`).

**Data provenance:** title/artist/genre for MusicBrainz-sourced songs are real. MusicBrainz has no
audio-analysis data at all, so `mood`/`energy`/`valence`/`danceability`/`acousticness`
are rough, deterministic **genre-level estimates** (e.g. "metal" → high energy, low valence, low
acousticness), not measured values — see the estimate table and reasoning in `src/musicbrainz.py`.

### Running the CLI

```bash
python -m src.main
```

### Running the Streamlit app

```bash
streamlit run app.py
```

If `streamlit` isn't recognized as a command (common on Windows, especially with the Python
Store install), run it as a module instead — this always works as long as `pip install -r
requirements.txt` succeeded:

```bash
python -m streamlit run app.py
```

Lets you set your taste profile with sliders/selects (populated from the actual catalog) instead
of editing the hardcoded profile in `main.py`, and includes a session-only password field to try
a Claude API key without setting up `.env` at all.

### Running Tests

```bash
python -m pytest
```

This runs the baseline profile tests (`tests/test_recommender.py`, exercising the real
`score_song()`/`recommend_songs()` pipeline against the three listener archetypes in
`src/test_profiles.py`) and the full adversarial regression suite (`tests/test_adversarial.py`),
which exercises all 8 edge-case profiles from `src/adversarial_profiles.py` against the real
pipeline — 21 tests total.

### Running the Evaluation Harness

In addition to the pytest suite, a standalone evaluation script runs the same baseline and
adversarial profiles and prints a plain pass/fail summary without needing pytest installed:

```bash
python -m src.evaluate
```

```
======================================================================
MUSIC RECOMMENDER -- EVALUATION HARNESS
======================================================================
[PASS] baseline:High-Energy Pop Enthusiast -- baseline profile returns 5 ranked recommendations
[PASS] baseline:HIGH_ENERGY_POP top match -- top result for a pop/happy profile is itself pop and happy
[PASS] adversarial:PERFECTIONIST guardrail fires -- strict-tolerance warnings fire for all three numerical features
[PASS] adversarial:ACOUSTIC_PARADOX guardrail fires -- acoustic/energy paradox warning fires when both are set
...
----------------------------------------------------------------------
SUMMARY: 17/17 checks passed (100% confidence)
----------------------------------------------------------------------
```

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

**A second example** — swapping in the `ACOUSTIC_PARADOX` adversarial profile
(`likes_acoustic=True` with `target_energy=0.95`, from `src/adversarial_profiles.py`) shows the
guardrail layer actually firing in the primary demo path, not just in tests:

```
======================================================================
GUARDRAIL WARNINGS
======================================================================
  ! likes_acoustic=True with target_energy (0.95) is a paradox -- acoustic songs are typically
    low-energy, so the acoustic bonus and the energy target will often conflict

======================================================================
TOP 5 MUSIC RECOMMENDATIONS
======================================================================

1. Sunrise City
   Artist: Neon Echo | Genre: pop | Mood: happy
   Score: 7.14/12.0 [#################-------------]
   Why matched:
     - mood match (+1.5)
     - valence within range (+2.4)
     - energy within range (+2.0)
     - danceability within range (+1.2)
   AI Explanation: mood match, valence within range, energy within range, danceability within range
----------------------------------------------------------------------

2. Morning Mist
   Artist: Acoustic Wanderers | Genre: folk | Mood: nostalgic
   Score: 7.00/12.0 [#################-------------]
   Why matched:
     - genre match (+2.0)
     - valence within range (+1.2)
     - energy within range (+1.2)
     - danceability within range (+0.6)
     - acoustic bonus (+2.0)
   AI Explanation: genre match, valence within range, energy within range, danceability within range, acoustic bonus
----------------------------------------------------------------------
```

Note the guardrail warning is correct: the acoustic bonus never actually lands on the top pick
("Sunrise City" isn't acoustic) because no high-acousticness song in this catalog also hits a
0.95 energy target — exactly the conflict the warning describes.

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

- Catalog size depends entirely on how much you've imported via `manage_songs.py`; a small or
  narrow-genre catalog means strict profiles can exhaust the meaningfully-different options
  quickly (see `model_card.md`'s evaluation history, captured against the original 17-song fixture).
- No understanding of lyrics, language, or actual audio — everything is numeric metadata, and for
  MusicBrainz-sourced songs that metadata (mood, energy, valence, danceability, acousticness) is
  itself a rough genre-level *estimate*, not a measurement — see `src/musicbrainz.py`. Two songs in
  the same genre get slightly different values (a small deterministic per-song nudge), but neither
  reflects how that specific recording actually sounds.
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
surfaced, what was fixed, and what's left as future work — including a dedicated section (§12)
on how AI was used during development, one helpful and one flawed AI suggestion, and current
system limitations.

Building the guardrail layer made it clear how much of "recommender quality" is really about
handling the profiles a system *shouldn't* have to handle gracefully — a contradictory or
degenerate preference shouldn't crash anything or silently produce nonsense, it should say so.
Wiring in the RAG explanation layer showed the flip side of that lesson: a generative layer needs
the same discipline, which is why it's restricted to only the data actually retrieved for that
song rather than left free to describe the music however it likes.
