# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Explain your design in plain language.
Each song will use these attributes:
  - ID, Itle, Artist, Genre, Mood, Energy, Tempo_BPM, Valence, Danceability, Acousticness.
These main atributes will be imporant in classifying each  song to allow the application to better recommend songs based on attribute similarity.

Each UserProfile will use these attributes:
  - Favorite_Genre, Favorite_Mood, Target_Energy, Likes_Acoustic

  From both these main factors, we will be able to create a score_song() function in which each song is given a score of compatibility between each user based off on how likely they are to like said song, and whether we should recommend it or not.

  In addition to this, we will construct our song similarity algorithm with the following parameters:

  Genre match,	+2.0, This is the most reliable predictor.
  Mood match,	+1.0,	Less stable than genre as users tolerate mood variation more.
  Energy similarity,	0.0 to +1.5,	Based on how close the song's energy is to the target.
---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output
```
5. Velvet Dreams
   Artist: Soul Collective | Genre: soul | Mood: romantic
   Score: 5.60/12.0 [██████████████░░░░░░░░░░░░░░░░]
   Why matched:
     • valence within range (+2.4)
     • energy within range (+2.0)
     • danceability within range (+1.2)
```
====================================================================
TOP 5 MUSIC RECOMMENDATIONS
======================================================================
'''
1. Rooftop Lights
   Artist: Indigo Parade | Genre: indie pop | Mood: happy
   Score: 9.10/12.0 [██████████████████████░░░░░░░░]
   Why matched:
     • genre match (+2.0)
     • mood match (+1.5)
     • valence within range (+2.4)
     • energy within range (+2.0)
     • danceability within range (+1.2)
----------------------------------------------------------------------
'''
'''
2. Sunrise City
   Artist: Neon Echo | Genre: pop | Mood: happy
   Score: 7.10/12.0 [█████████████████░░░░░░░░░░░░░]
   Why matched:
     • mood match (+1.5)
     • valence within range (+2.4)
     • energy within range (+2.0)
     • danceability within range (+1.2)
----------------------------------------------------------------------
'''
'''
3. Gym Hero
   Artist: Max Pulse | Genre: pop | Mood: intense
   Score: 5.60/12.0 [██████████████░░░░░░░░░░░░░░░░]
   Why matched:
     • valence within range (+2.4)
     • energy within range (+2.0)
     • danceability within range (+1.2)
----------------------------------------------------------------------
'''
'''
4. Electric Pulse
   Artist: Neon Beats | Genre: electronic | Mood: energetic
   Score: 5.60/12.0 [██████████████░░░░░░░░░░░░░░░░]
   Why matched:
     • valence within range (+2.4)
     • energy within range (+2.0)
     • danceability within range (+1.2)
----------------------------------------------------------------------
'''
'''
5. Velvet Dreams
   Artist: Soul Collective | Genre: soul | Mood: romantic
   Score: 5.60/12.0 [██████████████░░░░░░░░░░░░░░░░]
   Why matched:
     • valence within range (+2.4)
     • energy within range (+2.0)
     • danceability within range (+1.2)
----------------------------------------------------------------------
'''
**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



