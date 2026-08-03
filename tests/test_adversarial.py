"""
Automated regression suite over the adversarial user profiles.

These profiles (src/adversarial_profiles.py) were originally a standalone
script you had to run and eyeball by hand. This file makes them part of the
normal `pytest` run: every profile is exercised through the real
recommend_songs()/validate_profile() pipeline, and the specific bugs
model_card.md documented (perfectionist tolerance collapse, zero-weight
degeneration, conflicting-emotion mismatches, the acoustic/energy paradox)
are asserted against directly, so a regression trips a test instead of
requiring someone to notice weird output.
"""

import math

import pytest

from src.adversarial_profiles import (
    ALL_ADVERSARIAL_PROFILES,
    CONFLICTING_EMOTIONS,
    PERFECTIONIST,
    NO_FEATURES,
    ACOUSTIC_PARADOX,
)
from src.guardrails import validate_profile
from src.recommender import load_songs, recommend_songs


@pytest.fixture(scope="module")
def catalog():
    return load_songs("data/songs.csv")


@pytest.mark.parametrize(
    "profile",
    ALL_ADVERSARIAL_PROFILES,
    ids=[p["profile_name"] for p in ALL_ADVERSARIAL_PROFILES],
)
def test_adversarial_profile_never_crashes_and_stays_bounded(profile, catalog):
    """Every adversarial profile should produce a well-formed result, never raise."""
    result = recommend_songs(profile, catalog, k=5)

    assert 0 <= len(result.items) <= 5

    for song, score, explanation, reasons in result.items:
        assert math.isfinite(score)
        assert score >= 0.0
        assert isinstance(explanation, str)
        assert isinstance(reasons, list) and len(reasons) > 0


def test_perfectionist_strict_tolerance_still_returns_k_songs(catalog):
    """A 17-song catalog should still yield 5 results even with 0.05 tolerance bands."""
    result = recommend_songs(PERFECTIONIST, catalog, k=5)
    assert len(result.items) == 5


def test_perfectionist_tolerance_bands_trigger_guardrail_warnings(catalog):
    warnings = validate_profile(PERFECTIONIST, catalog)
    assert any("energy_tolerance" in w for w in warnings)
    assert any("valence_tolerance" in w for w in warnings)
    assert any("danceability_tolerance" in w for w in warnings)


def test_no_features_zero_weights_trigger_guardrail_warning(catalog):
    warnings = validate_profile(NO_FEATURES, catalog)
    assert any("zero" in w for w in warnings)


def test_conflicting_emotions_triggers_guardrail_warning(catalog):
    warnings = validate_profile(CONFLICTING_EMOTIONS, catalog)
    assert any("target_valence" in w for w in warnings)


def test_acoustic_paradox_triggers_guardrail_warning(catalog):
    warnings = validate_profile(ACOUSTIC_PARADOX, catalog)
    assert any("likes_acoustic" in w for w in warnings)


def test_negative_genres_wiping_out_catalog_falls_back_instead_of_returning_nothing(catalog):
    """If negative_genres would exclude every song, recommend_songs should still
    return a ranked list (from the unfiltered catalog) rather than silently
    returning zero results, and it should say so in the warnings."""
    catalog_genres = {song["genre"] for song in catalog}
    profile = {
        "favorite_genre": "indie pop",
        "favorite_mood": "happy",
        "target_energy": 0.5,
        "target_valence": 0.5,
        "target_danceability": 0.5,
        "negative_genres": list(catalog_genres),
    }

    result = recommend_songs(profile, catalog, k=5)

    assert len(result.items) == 5
    assert any("excluded every song" in w for w in result.warnings)
