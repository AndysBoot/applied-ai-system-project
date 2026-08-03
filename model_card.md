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
    - If not, add only hald the intended feature score
4) Acoustic bonus is given if the song is very acoustic(>0.7) and if you like acoustic music
5) We then sort all songs by their total score nd return the top 5
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
1) Smooth tolerance bands instead of cliifs
    - Use a gradual penalty that decreases smoothly rather then completely falling off
2) Make acoustic a feature, not a bonus
    - Let users set a acoustic bonus rather then giving it a flat out +2.0 bonus.
3) Validate and fix contradictions
    - One way this can be fixed is by offering suggestions to users so they can adjust their preferences.
---

## 9. Personal Reflection  
One of the things that surprised me the most was how easy but hard it was to design the recommendation algorithm.

Creating a scoring system that recommends songs to users wasn't complicated, but perfecting that system and making sure that edge cases were tken care of was.

It goes to show how much time and consideration is put into modern music recommendation algorithms like spotify and etc.
I 
