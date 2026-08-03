# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

MusicRecommender.exe 

---

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
