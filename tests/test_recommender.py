"""
Baseline profile tests for the real recommendation pipeline.

Exercises src.recommender.recommend_songs()/score_song() -- the same
dict-based functions used by src/main.py and app.py -- against the three
baseline listener archetypes in src/test_profiles.py.
"""

import math

import pytest

from src.recommender import load_songs, recommend_songs, score_song
from src.test_profiles import ALL_PROFILES, HIGH_ENERGY_POP, CHILL_LOFI, DEEP_INTENSE_ROCK


@pytest.fixture(scope="module")
def catalog():
    return load_songs("data/songs.csv")


@pytest.mark.parametrize(
    "profile",
    ALL_PROFILES,
    ids=[p["profile_name"] for p in ALL_PROFILES],
)
def test_baseline_profile_returns_well_formed_ranked_results(profile, catalog):
    """Every baseline profile should return k well-formed, score-sorted results."""
    result = recommend_songs(profile, catalog, k=5)

    assert len(result.items) == 5

    scores = [score for _, score, _, _ in result.items]
    assert scores == sorted(scores, reverse=True)
    for score in scores:
        assert math.isfinite(score)
        assert score >= 0.0


def test_high_energy_pop_top_result_matches_genre_and_mood(catalog):
    """The top match for a pop/happy profile should actually be pop and happy --
    the highest fixed-point bonuses in the scoring model."""
    result = recommend_songs(HIGH_ENERGY_POP, catalog, k=5)
    top_song, _, _, _ = result.items[0]

    assert top_song["genre"] == "pop"
    assert top_song["mood"] == "happy"


def test_high_energy_pop_excludes_negative_genres(catalog):
    result = recommend_songs(HIGH_ENERGY_POP, catalog, k=17)
    genres = {song["genre"] for song, _, _, _ in result.items}
    assert genres.isdisjoint(set(HIGH_ENERGY_POP["negative_genres"]))


def test_chill_lofi_favors_low_energy_acoustic_songs(catalog):
    """CHILL_LOFI targets low energy (0.30) with an acoustic bonus -- its top
    pick should be noticeably lower energy than DEEP_INTENSE_ROCK's top pick."""
    lofi_top, _, _, _ = recommend_songs(CHILL_LOFI, catalog, k=5).items[0]
    rock_top, _, _, _ = recommend_songs(DEEP_INTENSE_ROCK, catalog, k=5).items[0]

    assert lofi_top["energy"] < rock_top["energy"]


def test_score_song_returns_finite_score_and_nonempty_reasons(catalog):
    for song in catalog:
        score, reasons = score_song(HIGH_ENERGY_POP, song)
        assert math.isfinite(score)
        assert isinstance(reasons, list) and len(reasons) > 0
