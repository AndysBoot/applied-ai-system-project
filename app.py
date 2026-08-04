"""
Streamlit UI for the Music Recommender.

Run with: streamlit run app.py

This is a thin UI layer over the exact same pipeline the CLI (src/main.py)
uses -- src.recommender.recommend_songs() (guardrails + smoothed scoring)
and src.explain.generate_explanation() (RAG over the catalog, with a
deterministic fallback). No recommendation logic lives in this file.
"""

import logging
import os

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; ANTHROPIC_API_KEY can also be set directly in the environment

from src.recommender import load_songs_smart, recommend_songs
from src.explain import generate_explanations_batch

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

st.set_page_config(page_title="Music Recommender", page_icon="🎵", layout="centered")


@st.cache_data
def get_catalog():
    return load_songs_smart("data/songs.csv")


def main() -> None:
    try:
        songs = get_catalog()
    except RuntimeError as e:
        st.error(str(e))
        return
    genres = sorted({song["genre"] for song in songs})
    moods = sorted({song["mood"] for song in songs})

    st.title("🎵 Music Recommender")
    st.caption(
        "Rule-based scoring with a guardrail layer that flags contradictory "
        "preferences, plus an optional Claude-generated explanation grounded "
        "in the catalog."
    )

    with st.sidebar:
        st.header("Claude API key (optional)")
        key_input = st.text_input(
            "ANTHROPIC_API_KEY",
            type="password",
            help="Kept in memory for this session only, never written to disk. "
            "Leave blank to use the deterministic explanation instead of live Claude calls.",
        )
        if key_input:
            os.environ["ANTHROPIC_API_KEY"] = key_input

        if os.environ.get("ANTHROPIC_API_KEY"):
            st.success("RAG explanations active")
        else:
            st.info("No key set — explanations will use the deterministic fallback")

    with st.form("preferences"):
        st.subheader("Your taste profile")

        col1, col2 = st.columns(2)
        with col1:
            favorite_genre = st.selectbox("Favorite genre", genres)
            favorite_mood = st.selectbox("Favorite mood", moods)
            k = st.slider("How many recommendations?", 1, 10, 5)
        with col2:
            likes_acoustic = st.checkbox("I like acoustic songs")
            acoustic_strength = st.slider(
                "Acoustic bonus strength", 0.0, 2.0, 0.6, disabled=not likes_acoustic
            )
            negative_genres = st.multiselect("Genres to avoid", genres)

        st.markdown("**Targets** (0 = low, 1 = high) and how much deviation to tolerate")
        t1, t2, t3 = st.columns(3)
        with t1:
            target_energy = st.slider("Target energy", 0.0, 1.0, 0.75)
            energy_tolerance = st.slider("Energy tolerance", 0.01, 0.5, 0.15)
        with t2:
            target_valence = st.slider("Target valence (happiness)", 0.0, 1.0, 0.80)
            valence_tolerance = st.slider("Valence tolerance", 0.01, 0.5, 0.15)
        with t3:
            target_danceability = st.slider("Target danceability", 0.0, 1.0, 0.75)
            danceability_tolerance = st.slider("Danceability tolerance", 0.01, 0.5, 0.10)

        st.markdown("**Feature weights** (relative importance)")
        w1, w2, w3 = st.columns(3)
        with w1:
            weight_valence = st.slider("Valence weight", 0.0, 1.0, 0.30)
        with w2:
            weight_energy = st.slider("Energy weight", 0.0, 1.0, 0.25)
        with w3:
            weight_danceability = st.slider("Danceability weight", 0.0, 1.0, 0.15)

        submitted = st.form_submit_button("Get recommendations")

    if not submitted:
        st.info("Set your preferences above and click **Get recommendations**.")
        return

    user_prefs = {
        "favorite_genre": favorite_genre,
        "favorite_mood": favorite_mood,
        "target_energy": target_energy,
        "target_valence": target_valence,
        "target_danceability": target_danceability,
        "energy_tolerance": energy_tolerance,
        "valence_tolerance": valence_tolerance,
        "danceability_tolerance": danceability_tolerance,
        "feature_weights": {
            "valence": weight_valence,
            "energy": weight_energy,
            "danceability": weight_danceability,
        },
        "likes_acoustic": likes_acoustic,
        "acoustic_preference_strength": acoustic_strength,
        "negative_genres": negative_genres,
    }

    result = recommend_songs(user_prefs, songs, k=k)

    if result.warnings:
        st.subheader("⚠️ Guardrail warnings")
        for warning in result.warnings:
            st.warning(warning)

    st.subheader(f"Top {len(result.items)} recommendations")

    # All explanations for this result set are generated in a single Claude call.
    explain_items = [(song, score, reasons) for song, score, _, reasons in result.items]
    with st.spinner("Generating explanations..."):
        ai_explanations = generate_explanations_batch(user_prefs, explain_items, songs)

    for idx, ((song, score, explanation, reasons), ai_explanation) in enumerate(
        zip(result.items, ai_explanations), 1
    ):
        with st.container(border=True):
            st.markdown(f"**{idx}. {song['title']}** — {song['artist']}")
            st.caption(f"Genre: {song['genre']} | Mood: {song['mood']}")
            st.progress(min(1.0, max(0.0, score / 12.0)), text=f"Score: {score:.2f}/12.0")

            with st.expander("Why matched"):
                for reason in reasons:
                    st.write(f"- {reason}")

            st.markdown(f"_{ai_explanation}_")


if __name__ == "__main__":
    main()
