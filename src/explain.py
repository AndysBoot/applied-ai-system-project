"""
RAG-powered explanation layer.

Retrieves grounding data for each recommended song -- its own attributes plus
a couple of catalog songs sharing its genre or mood -- and asks Claude to turn
that, together with the deterministic scoring reasons, into a short natural
language explanation per song. The model is explicitly forbidden from
inventing facts not present in the retrieved data.

Cost note: all k recommendations for a run are explained in a SINGLE Claude
call (generate_explanations_batch), not one call per song. That's the biggest
lever for keeping this cheap -- it avoids repeating the shared listener-
preferences preamble k times, and Haiku 4.5 (the cheapest current model) plus
a tight max_tokens budget keep each run to a small, fixed amount of output.

If no API key is configured, the `anthropic` package isn't installed, or the
API call fails or returns something unparseable, this always falls back to
the existing deterministic explanation string per song. Callers never need to
branch on success/failure -- the batch call always returns one usable string
per input song.
"""

from typing import Dict, List, Tuple
import json
import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_COMPARISON_SONGS = 2
TOKENS_PER_SONG = 60
BASE_TOKENS = 40


def _deterministic_explanation(reasons: List[str]) -> str:
    """The original templated explanation, used whenever the RAG path is unavailable."""
    return ", ".join(reason.split("(")[0].strip() for reason in reasons)


def _retrieve_comparison_songs(song: Dict, catalog: List[Dict]) -> List[Dict]:
    """Pull a couple of other catalog songs sharing genre or mood, for grounding context."""
    matches = [
        other for other in catalog
        if other["id"] != song["id"] and (other["genre"] == song["genre"] or other["mood"] == song["mood"])
    ]
    return matches[:MAX_COMPARISON_SONGS]


def _build_batch_prompt(
    user_prefs: Dict,
    items: List[Tuple[Dict, float, List[str]]],
    catalog: List[Dict],
) -> str:
    songs_block = []
    for idx, (song, score, reasons) in enumerate(items):
        comparisons = _retrieve_comparison_songs(song, catalog)
        comparison_line = "; ".join(
            f"\"{c['title']}\" ({c['genre']}/{c['mood']})" for c in comparisons
        ) or "none"
        songs_block.append(
            f"{idx}. \"{song['title']}\" by {song['artist']} -- genre={song['genre']}, "
            f"mood={song['mood']}, energy={song['energy']}, valence={song['valence']}, "
            f"danceability={song['danceability']}, acousticness={song['acousticness']}, "
            f"score={score:.2f}/12.0, reasons=[{'; '.join(reasons)}], "
            f"similar_catalog_songs=[{comparison_line}]"
        )

    return f"""A music recommender scored {len(items)} songs for a listener. For EACH
song below, write ONE warm, concrete 1-sentence explanation of why it suits them, using
ONLY the facts given for that song. Do not invent attributes, artists, lyrics, or claims
not present in the data. Do not recommend the "similar_catalog_songs" instead -- they're
grounding context only.

Listener preferences:
- favorite_genre: {user_prefs.get('favorite_genre')}
- favorite_mood: {user_prefs.get('favorite_mood')}
- target_energy: {user_prefs.get('target_energy')}
- target_valence: {user_prefs.get('target_valence')}
- likes_acoustic: {user_prefs.get('likes_acoustic')}

Songs:
{chr(10).join(songs_block)}

Respond with ONLY a JSON array of {len(items)} strings, one explanation per song in the
same order, no other text. Example: ["explanation 0", "explanation 1", ...]
"""


def generate_explanations_batch(
    user_prefs: Dict,
    items: List[Tuple[Dict, float, List[str]]],
    catalog: List[Dict],
) -> List[str]:
    """Return one grounded natural-language explanation per (song, score, reasons) in items.

    Makes at most ONE Claude call for the whole batch. Always returns a list the
    same length as items, filled with the deterministic fallback wherever the
    RAG path is unavailable or fails.
    """
    fallbacks = [_deterministic_explanation(reasons) for _, _, reasons in items]
    if not items:
        return fallbacks

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.info("ANTHROPIC_API_KEY not set; using deterministic explanations for this batch")
        return fallbacks

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed; using deterministic explanations for this batch")
        return fallbacks

    prompt = _build_batch_prompt(user_prefs, items, catalog)
    max_tokens = BASE_TOKENS + TOKENS_PER_SONG * len(items)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()

        # Models sometimes wrap JSON in a code fence despite instructions; strip it defensively.
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        explanations = json.loads(text)
        if not isinstance(explanations, list) or len(explanations) != len(items):
            raise ValueError(f"expected a JSON array of {len(items)} strings, got: {text[:200]!r}")
        return [str(e).strip() or fb for e, fb in zip(explanations, fallbacks)]
    except Exception as exc:  # any API/parse failure should degrade gracefully, not crash the CLI
        logger.warning("batch RAG explanation call failed (%s); using deterministic explanations", exc)
        return fallbacks


def generate_explanation(
    user_prefs: Dict,
    song: Dict,
    score: float,
    reasons: List[str],
    catalog: List[Dict],
) -> str:
    """Single-song convenience wrapper over generate_explanations_batch (one Claude call)."""
    return generate_explanations_batch(user_prefs, [(song, score, reasons)], catalog)[0]
