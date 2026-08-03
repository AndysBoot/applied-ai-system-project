"""
RAG-powered explanation layer.

Retrieves grounding data for a recommended song -- its own attributes plus a
few catalog songs sharing its genre or mood -- and asks Claude to turn that,
together with the deterministic scoring reasons, into a short natural
language explanation. The model is explicitly forbidden from inventing facts
not present in the retrieved data.

If no API key is configured, the `anthropic` package isn't installed, or the
API call fails for any reason, this always falls back to the existing
deterministic explanation string. Callers never need to branch on
success/failure -- generate_explanation() always returns a usable string.
"""

from typing import Dict, List
import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_COMPARISON_SONGS = 3
MAX_TOKENS = 150


def _deterministic_explanation(reasons: List[str]) -> str:
    """The original templated explanation, used whenever the RAG path is unavailable."""
    return ", ".join(reason.split("(")[0].strip() for reason in reasons)


def _retrieve_comparison_songs(song: Dict, catalog: List[Dict]) -> List[Dict]:
    """Pull a few other catalog songs sharing genre or mood, for grounding context."""
    matches = [
        other for other in catalog
        if other["id"] != song["id"] and (other["genre"] == song["genre"] or other["mood"] == song["mood"])
    ]
    return matches[:MAX_COMPARISON_SONGS]


def _build_prompt(user_prefs: Dict, song: Dict, score: float, reasons: List[str], comparison_songs: List[Dict]) -> str:
    comparison_lines = "\n".join(
        f"- \"{c['title']}\" by {c['artist']}: genre={c['genre']}, mood={c['mood']}, "
        f"energy={c['energy']}, valence={c['valence']}, danceability={c['danceability']}"
        for c in comparison_songs
    ) or "(no comparable songs in the catalog)"

    return f"""A music recommender scored the song below for a listener. Write a warm,
concrete 1-2 sentence explanation of why this song suits them, using ONLY the facts
given below. Do not invent attributes, artists, lyrics, or claims not present in this data.

Listener preferences:
- favorite_genre: {user_prefs.get('favorite_genre')}
- favorite_mood: {user_prefs.get('favorite_mood')}
- target_energy: {user_prefs.get('target_energy')}
- target_valence: {user_prefs.get('target_valence')}
- likes_acoustic: {user_prefs.get('likes_acoustic')}

Recommended song:
- title: {song['title']}
- artist: {song['artist']}
- genre: {song['genre']}
- mood: {song['mood']}
- energy: {song['energy']}
- valence: {song['valence']}
- danceability: {song['danceability']}
- acousticness: {song['acousticness']}
- score: {score:.2f}/12.0
- scoring reasons: {'; '.join(reasons)}

Similar songs in the catalog (for context only, do not recommend these instead):
{comparison_lines}
"""


def generate_explanation(
    user_prefs: Dict,
    song: Dict,
    score: float,
    reasons: List[str],
    catalog: List[Dict],
) -> str:
    """Return a grounded natural-language explanation, or the deterministic fallback.

    Retrieval: song's own attributes + up to MAX_COMPARISON_SONGS catalog songs
    sharing its genre or mood. Generation: Claude, prompted to use only that
    retrieved data. Always returns a non-empty string -- never raises.
    """
    fallback = _deterministic_explanation(reasons)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.info("ANTHROPIC_API_KEY not set; using deterministic explanation for '%s'", song["title"])
        return fallback

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed; using deterministic explanation for '%s'", song["title"])
        return fallback

    comparison_songs = _retrieve_comparison_songs(song, catalog)
    prompt = _build_prompt(user_prefs, song, score, reasons, comparison_songs)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()
        if not text:
            raise ValueError("empty response from Claude")
        return text
    except Exception as exc:  # any API failure should degrade gracefully, not crash the CLI
        logger.warning("RAG explanation call failed for '%s' (%s); using deterministic explanation", song["title"], exc)
        return fallback
