"""
Smart template-based explanation layer for music recommendations.

Generates natural-sounding explanations by analyzing the scoring patterns
and song attributes. No API keys required, fully deterministic, and always
produces contextual feedback on why a song was recommended.

The explanation system:
1. Parses the scoring reasons to identify what matched (genre, mood, features)
2. Analyzes the song attributes (energy, valence, danceability, acousticness)
3. Selects appropriate templates based on the match pattern
4. Fills templates with actual song/preference data for natural explanations
"""

from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


def _parse_reasons(reasons: List[str]) -> Dict[str, bool]:
    """Identify what factors matched based on the scoring reasons."""
    matches = {
        "genre_match": False,
        "mood_match": False,
        "energy_match": False,
        "valence_match": False,
        "danceability_match": False,
        "acoustic_bonus": False,
    }

    reason_text = " ".join(reasons).lower()

    if "genre" in reason_text and "match" in reason_text:
        matches["genre_match"] = True
    if "mood" in reason_text and "match" in reason_text:
        matches["mood_match"] = True
    if "energy" in reason_text:
        matches["energy_match"] = True
    if "valence" in reason_text or "happiness" in reason_text:
        matches["valence_match"] = True
    if "danceability" in reason_text:
        matches["danceability_match"] = True
    if "acoustic" in reason_text:
        matches["acoustic_bonus"] = True

    return matches


def _get_attribute_description(value: float, attribute: str) -> str:
    """Convert a numeric attribute value to a descriptive phrase."""
    descriptions = {
        "energy": {
            "low": ("mellow", "laid-back", "gentle"),
            "mid": ("balanced", "moderate"),
            "high": ("energetic", "dynamic", "vibrant"),
        },
        "valence": {
            "low": ("melancholic", "introspective", "contemplative"),
            "mid": ("balanced mood"),
            "high": ("upbeat", "joyful", "happy"),
        },
        "danceability": {
            "low": ("groove-light"),
            "mid": ("danceable"),
            "high": ("highly danceable", "groove-heavy"),
        },
        "acousticness": {
            "low": ("polished", "produced"),
            "mid": ("blend of"),
            "high": ("organic", "acoustic"),
        },
    }

    if value < 0.4:
        level = "low"
    elif value < 0.7:
        level = "mid"
    else:
        level = "high"

    options = descriptions.get(attribute, {}).get(level, ("moderate",))
    return options[0]  # Return first variant


def _build_smart_explanation(
    user_prefs: Dict,
    song: Dict,
    score: float,
    reasons: List[str],
) -> str:
    """Generate a contextual explanation based on song attributes and match patterns."""

    matches = _parse_reasons(reasons)
    favorite_genre = user_prefs.get("favorite_genre", "your preferred genre")
    favorite_mood = user_prefs.get("favorite_mood", "your mood")

    song_title = song.get("title", "This track")
    song_genre = song.get("genre", "")
    song_mood = song.get("mood", "")
    energy = song.get("energy", 0.5)
    valence = song.get("valence", 0.5)
    danceability = song.get("danceability", 0.5)
    acousticness = song.get("acousticness", 0.5)

    energy_desc = _get_attribute_description(energy, "energy")
    valence_desc = _get_attribute_description(valence, "valence")
    dance_desc = _get_attribute_description(danceability, "danceability")
    acoustic_desc = _get_attribute_description(acousticness, "acousticness")

    # Template selection based on what matched
    if matches["genre_match"] and matches["mood_match"] and matches["energy_match"]:
        # Perfect triple match: high confidence
        templates = [
            f"{song_title} nails your taste—it's {song_genre} with {valence_desc} vibes and {energy_desc} energy, exactly in your wheelhouse.",
            f"This {song_genre} track delivers the {valence_desc}, {energy_desc} experience you're looking for, making it a natural fit for your preferences.",
            f"With its {valence_desc} mood and {energy_desc} character, {song_title} is a perfect alignment with your {favorite_genre} taste.",
        ]
    elif matches["genre_match"] and matches["mood_match"]:
        # Genre and mood match but maybe not all features
        templates = [
            f"{song_title} is a {song_genre} gem with a {valence_desc} vibe that matches your style perfectly.",
            f"As a {song_genre} track with {valence_desc} energy, this one resonates with your {favorite_mood} mood preference.",
            f"This {song_genre} song captures the {valence_desc}, {favorite_mood} essence you're drawn to.",
        ]
    elif matches["genre_match"]:
        # Genre match is the main driver
        templates = [
            f"{song_title} brings a fresh take on {song_genre} with its {energy_desc}, {valence_desc} character.",
            f"This is a stellar example of {song_genre}—with {valence_desc} vibes and a {energy_desc} groove that stands out.",
            f"As a standout {song_genre} track, {song_title} delivers the energy and mood you're seeking.",
        ]
    elif matches["energy_match"] and matches["danceability_match"]:
        # Energy and danceability focused
        templates = [
            f"{song_title} hits the sweet spot with its {energy_desc} energy and {dance_desc} rhythm, perfect for your preferences.",
            f"This track's {energy_desc} drive and {dance_desc} pulse align beautifully with what you're looking for.",
            f"The {energy_desc}, {dance_desc} character of this {song_genre} song makes it a great match for you.",
        ]
    elif matches["acoustic_bonus"]:
        # Acoustic focus
        templates = [
            f"{song_title} brings an {acoustic_desc} quality with {valence_desc} emotion, adding a natural touch to your recommendations.",
            f"This {acoustic_desc} {song_genre} track has a warm, genuine feel that complements your taste.",
            f"The organic, {acoustic_desc} character of {song_title} gives it a special appeal for you.",
        ]
    else:
        # Fallback: general good match
        templates = [
            f"{song_title} is a strong recommendation—its {energy_desc} energy, {valence_desc} mood, and {song_genre} style align well with your preferences.",
            f"This {song_genre} track delivers across multiple dimensions: {energy_desc} energy, {valence_desc} vibes, and genuine musical quality.",
            f"{song_title} combines the {valence_desc}, {energy_desc} character you want with solid musicianship in the {song_genre} space.",
        ]

    return templates[0]


def generate_explanations_batch(
    user_prefs: Dict,
    items: List[Tuple[Dict, float, List[str]]],
    catalog: List[Dict],
) -> List[str]:
    """Return one natural-language explanation per (song, score, reasons) in items.

    Uses smart template-based generation with no API keys required.
    Always returns a list the same length as items.
    """
    explanations = []

    for song, score, reasons in items:
        explanation = _build_smart_explanation(user_prefs, song, score, reasons)
        explanations.append(explanation)

    return explanations


def generate_explanation(
    user_prefs: Dict,
    song: Dict,
    score: float,
    reasons: List[str],
    catalog: List[Dict],
) -> str:
    """Single-song convenience wrapper over generate_explanations_batch."""
    return generate_explanations_batch(user_prefs, [(song, score, reasons)], catalog)[0]
