# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

MusicRecommender.exe 

---

> **Note on catalog evolution:** the concrete evaluation runs below (section 8/9) were captured
> against the original fixed 17-song `data/songs.csv` catalog, which is still used as-is by
> `tests/` for reproducible regression checks. The live app (`src/main.py`, `app.py`) no longer
> reads that CSV -- it loads exclusively from `data/songs.db`, a SQLite catalog populated with
> real songs from the MusicBrainz API (see `src/musicbrainz.py`,
> `scripts/manage_songs.py import-musicbrainz`). Title/artist/genre for those songs are real;
> MusicBrainz has no audio-analysis data, so mood/energy/valence/danceability/acousticness/tempo
> are rough, documented genre-level estimates rather than measured values. The specific numbers
> and song names below (catalog size 17, "Dusty Roads", etc.) describe that original test
> fixture, not the live catalog's current contents.

## 2. Intended Use  

This system gives music recommendations from a catalog based on wheat preferences you like. Some prefences are:
1) Favorite genre
2) Favorite mood
3) Your song energy level
4) Happy/Sad prefence
5) Danceability
---

## 3. How the Model Works  

The model works based off the following scoring system:
1) If the genre matches, add 2 points
2) If the mood matches, add 1.5 points
3) Checks if the song is within your tolerance
    - Is the song close enough to your energy, valence, or dnceability?
    - If so, add the full feature score
    - **Update:** originally, if it wasn't within tolerance we'd add only half the intended
      feature score straight away -- a hard cliff. That's fixed now (see Future Work item 1):
      the score decays smoothly the further out of tolerance a song is, instead of instantly
      dropping to half.
4) Acoustic bonus is given if the song is very acoustic(>0.7) and if you like acoustic music
5) We then sort all songs by their total score nd return the top 5
6) **New:** before any of this runs, a guardrail layer (`src/guardrails.py`) checks the
   profile itself for contradictions or degenerate settings (see section 10)
7) **New:** each recommended song also gets an AI-generated explanation grounded in its own
   data, with a deterministic fallback if no API key is set (see section 10)
---

## 4. Data  

Catalog size: 17 songs

Each song contains a title, artist, genre, mood, energy, valence, happiness, danceability, acousticness, tempo in BPM

---

## 5. Strengths  

One of the biggest strengths tha our model has is that genre-matched songs rank the highest out of all other sore factors. We also know that energy targets drive different recommendation sets.

## 6. Limitations and Bias 

Currently, my catalog has 35% low energy songs and 30% high energy songs, however the scoring treats them both equally which creates a systematic bias against low-energy seekers.
This leeds to three limitations:
1) High energy users get pulled into low-energy recommendations
2) A user wanting jazz + high energy is almost impossible to serve
3) Only one song has a mood = "focused", creating a filter bubble where users cant escape

---

## 7. Evaluation  

The application is currently robus against these 5 evaluations:
1) Correctness
2) RObustness
3) Fairness
4) Stability
5) Completeness

After fixing the  pefectionist tolerance bug, INDIFFERENT ranking collapse, energy gap bias, we were able to create a model that is great at recommending songs of best fit as long as they resie within the catalog.

Finally, some bugs that surprised me were the acoustic bonus, overriding targets, and contradcitions the algorithm attempted to handle.
---

## 8. Future Work  

Here are some fixes for the future
1) ~~Smooth tolerance bands instead of cliifs~~ **DONE.** `_tolerance_band_score()` in
   `src/recommender.py` now decays linearly from full score at the tolerance boundary down to
   a floor at twice the tolerance, instead of instantly falling off.
2) Make acoustic a feature, not a bonus
    - Let users set a acoustic bonus rather then giving it a flat out +2.0 bonus.
    - Still open -- the guardrail layer (section 10) now at least *warns* when
      `likes_acoustic=True` conflicts with a high energy target, but the scoring itself still
      treats acoustic as a flat bonus rather than a weighted feature.
3) ~~Validate and fix contradictions~~ **DONE, via warnings rather than auto-fixing.**
   `src/guardrails.py`'s `validate_profile()` detects contradictory/degenerate profiles
   (zero weights, conflicting energy/mood, overly strict tolerance, the acoustic/energy
   paradox, negative-genre lists that would empty the catalog) and logs/surfaces warnings.
   It deliberately does not auto-adjust the user's preferences -- the original idea of
   "offering suggestions" is still open future work if the warnings should also propose a
   fix instead of just describing the problem.
4) New: extend `validate_profile()` to catch genre/mood pairings that are rare in the actual
   catalog (not just the fixed thresholds it uses today), now that section 10's guardrail
   layer exists to build on.
---

## 9. Personal Reflection  
One of the things that surprised me the most was how easy but hard it was to design the recommendation algorithm.

Creating a scoring system that recommends songs to users wasn't complicated, but perfecting that system and making sure that edge cases were tken care of was.

It goes to show how much time and consideration is put into modern music recommendation algorithms like spotify and etc.
I 

---

## 10. Applied AI System Extensions

This model card originally covered a pure rule-based scorer. Two features were added on top of
it, both fully wired into `recommend_songs()`/`main.py`/`app.py` rather than standalone scripts:

**Guardrail / reliability layer** (`src/guardrails.py`) -- runs before scoring, on every call.
Checks the profile itself (not the catalog) for: all feature weights zero, high energy target
paired with low valence target, any tolerance band under 0.08, `likes_acoustic` paired with a
very high energy target, and a `negative_genres` list covering most of the catalog's genres. It
warns rather than blocks -- a bad profile still gets a recommendation, just an explainable one.
`tests/test_adversarial.py` turns the 8 profiles in `src/adversarial_profiles.py` into an
automated regression suite that asserts these warnings actually fire where expected, and that
the recommender never crashes or returns malformed scores for any of them.

**RAG explanation layer** (`src/explain.py`) -- retrieves the recommended song's own attributes
plus up to 3 catalog songs sharing its genre or mood, and asks Claude to write a short
explanation grounded only in that retrieved data (explicitly told not to invent facts). Falls
back to the original deterministic reason string if no API key is configured or the call fails,
so the system's core behavior (and its testability) doesn't depend on an external API being
available.

**Bug found while wiring these in:** `score_song` had been reading a generic `tolerance` key
that no profile actually sets -- every profile (including the adversarial ones) sets
`energy_tolerance`/`valence_tolerance`/`danceability_tolerance` instead. That means every
profile's per-feature tolerance had silently been a no-op since this project started; fixing it
changed the default profile's top-5 ranking. A good reminder that a "working" demo can still have
dead config fields that never actually influenced behavior.

**Dead code found and removed:** `src/recommender.py` also carried a second, unused
implementation -- a `Song`/`UserProfile`/`Recommender` class trio with `# TODO: Implement`
stubs (`recommend()` just returned `self.songs[:k]` unsorted; `explain_recommendation()`
returned a hardcoded placeholder string). `tests/test_recommender.py` was testing *that* stub,
not the real dict-based `score_song()`/`recommend_songs()` pipeline that `main.py` and `app.py`
actually call -- so the "baseline" tests were passing without ever exercising real scoring logic.
Both were removed/rewritten: the stub classes are gone, and `test_recommender.py` now runs the
three baseline profiles from `src/test_profiles.py` through the real pipeline (genre/mood match
on the top result, negative-genre exclusion, low-energy vs. high-energy ranking).

---

## 11. Guardrail Behavior — Input / Behavior / Result Examples

Concrete runs of `recommend_songs()` against the real 17-song catalog, showing what each
adversarial profile actually triggers (not just what it's designed to test for).

**PERFECTIONIST** -- `energy_tolerance`/`valence_tolerance`/`danceability_tolerance` all `0.05`
- **Input:** favorite_genre="indie", favorite_mood="happy", tolerance bands of 0.05 on all three numerical features
- **Behavior:** guardrail fires three separate "very strict" warnings (one per feature); scoring still runs the smoothed tolerance curve rather than a hard cliff
- **Result:** still returns all 5 requested songs (top: "Dusty Roads") -- the guardrail *warns* that results may be sparse, but the smoothed scoring means a small catalog doesn't actually run dry the way a hard-cliff score would

**NO_FEATURES** -- all `feature_weights` set to `0.0`
- **Input:** favorite_genre="indie pop", favorite_mood="happy", every numerical feature weight zero
- **Behavior:** guardrail fires "all numerical feature weights are zero" warning
- **Result:** 5 songs still returned (top: "Rooftop Lights"), ranking driven entirely by genre/mood bonuses since no numerical feature can differentiate songs -- exactly the degenerate-but-not-broken behavior the guardrail is meant to flag

**CONFLICTING_EMOTIONS** -- `target_energy=0.90`, `target_valence=0.20`
- **Input:** favorite_genre="rock", favorite_mood="melancholic", high energy target paired with low valence target
- **Behavior:** guardrail fires the "uncommon emotional combination" warning
- **Result:** 5 songs returned (top: "Storm Runner", a high-energy/low-valence rock track) -- the system still finds a sensible top match here because the catalog happens to contain that combination, but the warning correctly flags that this pairing is atypical and may not always be servable

**ACOUSTIC_PARADOX** -- `likes_acoustic=True`, `target_energy=0.95`
- **Input:** favorite_genre="folk", favorite_mood="happy", wants acoustic songs *and* very high energy
- **Behavior:** guardrail fires the acoustic/energy paradox warning
- **Result:** 5 songs returned (top: "Sunrise City", a non-acoustic pop track) -- the acoustic bonus never actually applies to the top pick because no high-acousticness song in the catalog also hits the energy target, which is exactly the conflict the warning describes

**Negative-genre catalog wipeout** -- `negative_genres` set to every genre in the catalog
- **Input:** a profile whose `negative_genres` list equals the full set of genres present in `data/songs.csv`
- **Behavior:** the hard filter would exclude all 17 songs; `recommend_songs()` detects the empty pool and falls back to the unfiltered catalog, logging an additional guardrail warning ("excluded every song in the catalog")
- **Result:** 5 songs still returned instead of an empty list -- covered directly by `tests/test_negative_genres_wiping_out_catalog_falls_back_instead_of_returning_nothing` in `tests/test_adversarial.py`

---

## 12. Reflection on AI Collaboration and System Design

This project was built with Claude Code as an active collaborator across design, debugging, and
testing -- not just for generating boilerplate.

**How AI was used:**
- **Design:** talked through how to fix the tolerance-band "cliff" (full score, then an instant
  drop to half) into something smoother, before implementing `_tolerance_band_score()`'s linear
  decay in `src/recommender.py`.
- **Debugging:** AI-assisted tracing of `score_song()` surfaced that it was reading a `tolerance`
  key no profile ever sets, instead of the `energy_tolerance`/`valence_tolerance`/
  `danceability_tolerance` keys every profile actually uses -- a silent no-op bug present since
  the original Module 3 version (see section 10).
- **Testing:** used AI to turn the `src/adversarial_profiles.py` cases -- originally a
  print-and-eyeball script -- into the automated `tests/test_adversarial.py` regression suite,
  and to audit `tests/test_recommender.py` for whether it was actually testing the real pipeline.

**One helpful suggestion:** the linear-decay tolerance smoothing (score falls off gradually from
the tolerance boundary to twice the tolerance, rather than instantly halving) was an AI suggestion
I hadn't considered -- I was originally planning to just widen the tolerance bands, which would
have masked the cliff rather than removing it. The smoothed version keeps rankings stable near the
boundary instead of swinging sharply between "just inside" and "just outside" a threshold.

**One flawed suggestion:** when designing the guardrail layer, an early AI suggestion was to have
`validate_profile()` *auto-correct* contradictory profiles (e.g., silently reweight a profile with
all-zero feature weights back to defaults) rather than just warn about them. I rejected this --
silently overriding a user's stated preferences hides what the system is actually doing and makes
its behavior harder to reason about. I kept the guardrail non-blocking and warning-only instead
(see Future Work item 3), which is a more honest contract with the caller even though it means a
"bad" profile can still produce a technically-valid-but-not-very-useful recommendation.

**Limitations and future improvements:** the guardrail thresholds (e.g. `STRICT_TOLERANCE_THRESHOLD
= 0.08`, `CONFLICTING_ENERGY_THRESHOLD = 0.70`) are hand-picked constants, not derived from the
actual catalog's distribution -- section 6's energy-distribution bias means some of these
thresholds may not generalize if the catalog grows or changes shape. The RAG explanation layer
also has no automated check that Claude's output stays grounded beyond the prompt instruction
itself; a stronger version would verify the generated text only references attributes present in
the retrieved data before showing it to the user, rather than trusting the prompt alone.
