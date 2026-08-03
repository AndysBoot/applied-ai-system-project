"""
Guardrail layer for the music recommender.

validate_profile() inspects a user preference dict *before* scoring and returns
human-readable warnings for contradictory or degenerate input. It never raises
and never blocks a recommendation from being produced -- the recommender stays
usable even for a "bad" profile, but the warnings get logged and surfaced to
the caller so the behavior is explainable rather than silently weird.

The checks below are drawn directly from the edge cases documented in
model_card.md and exercised by src/adversarial_profiles.py (conflicting
emotions, extreme tolerance bands, degenerate weights, massive negative-genre
lists, acoustic/energy paradox).
"""

from typing import Dict, List, Optional

ZERO_WEIGHT_EPSILON = 1e-9
STRICT_TOLERANCE_THRESHOLD = 0.08
CONFLICTING_ENERGY_THRESHOLD = 0.70
CONFLICTING_VALENCE_THRESHOLD = 0.35
ACOUSTIC_PARADOX_ENERGY_THRESHOLD = 0.85
NEGATIVE_GENRE_COVERAGE_WARNING_RATIO = 0.6


def validate_profile(user_prefs: Dict, songs: Optional[List[Dict]] = None) -> List[str]:
    """Return a list of warning strings for contradictory/degenerate profiles.

    `songs` is optional and only needed for the catalog-coverage check (how much
    of the actual genre pool a profile's negative_genres list would remove).
    """
    warnings: List[str] = []

    feature_weights = user_prefs.get("feature_weights", {})
    if feature_weights:
        total_weight = sum(feature_weights.values())
        if total_weight <= ZERO_WEIGHT_EPSILON:
            warnings.append(
                "all numerical feature weights are zero -- energy/valence/danceability "
                "will not differentiate songs; ranking will rely on genre/mood match only"
            )

    target_energy = user_prefs.get("target_energy")
    target_valence = user_prefs.get("target_valence")
    if target_energy is not None and target_valence is not None:
        if target_energy > CONFLICTING_ENERGY_THRESHOLD and target_valence < CONFLICTING_VALENCE_THRESHOLD:
            warnings.append(
                f"high target_energy ({target_energy:.2f}) combined with low target_valence "
                f"({target_valence:.2f}) is an uncommon emotional combination -- few songs in a "
                "typical catalog pair high energy with low happiness"
            )

    for band_name in ("energy_tolerance", "valence_tolerance", "danceability_tolerance"):
        band_value = user_prefs.get(band_name)
        if band_value is not None and band_value < STRICT_TOLERANCE_THRESHOLD:
            warnings.append(
                f"{band_name} is very strict ({band_value:.2f}) -- may return fewer than "
                "the requested number of recommendations"
            )

    if user_prefs.get("likes_acoustic") and target_energy is not None:
        if target_energy > ACOUSTIC_PARADOX_ENERGY_THRESHOLD:
            warnings.append(
                f"likes_acoustic=True with target_energy ({target_energy:.2f}) is a paradox -- "
                "acoustic songs are typically low-energy, so the acoustic bonus and the energy "
                "target will often conflict"
            )

    negative_genres = user_prefs.get("negative_genres", [])
    if negative_genres and songs:
        catalog_genres = {song["genre"] for song in songs}
        blocked_genres = catalog_genres & set(negative_genres)
        if catalog_genres:
            coverage_ratio = len(blocked_genres) / len(catalog_genres)
            if coverage_ratio >= NEGATIVE_GENRE_COVERAGE_WARNING_RATIO:
                warnings.append(
                    f"negative_genres excludes {len(blocked_genres)}/{len(catalog_genres)} "
                    "genres present in the catalog -- remaining song pool may be very small"
                )

    return warnings
