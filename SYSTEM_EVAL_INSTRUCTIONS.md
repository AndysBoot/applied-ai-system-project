# System Evaluation: Opening a New Chat Session

## Overview
This directory now contains all materials needed to conduct a thorough system evaluation of the music recommender. The evaluation should focus on edge cases, adversarial inputs, and potential failure modes.

## Files Prepared for Review

### Core Implementation
- **`src/recommender.py`** - Main scoring and recommendation functions
- **`src/main.py`** - CLI interface with visual output
- **`data/songs.csv`** - Song database

### Test Profiles
- **`src/test_profiles.py`** - Three baseline user profiles:
  - High-Energy Pop Enthusiast
  - Chill Lofi Relaxation  
  - Deep Intense Rock

- **`src/adversarial_profiles.py`** - Eight edge-case profiles:
  1. Conflicting Emotions (high energy + melancholic mood)
  2. Perfectionist (extremely strict tolerance 0.05)
  3. Indifferent (extremely loose tolerance 0.40)
  4. Genre-Mood Paradox (jazz + high-energy electronic)
  5. Energy Obsessed (energy weight 1.0, others 0)
  6. Picky Eater (10+ negative genres)
  7. Acoustic Paradox (likes acoustic but wants high-energy)
  8. No Features (all feature weights zero)

## How to Open a New Evaluation Chat Session

### Option 1: In Claude Code
1. Click **"New Chat"** or use the chat icon
2. Select or type a name: **"System Evaluation: Music Recommender"**
3. In the new chat, paste the section below marked **[PASTE INTO NEW CHAT]**

### Option 2: On claude.ai
1. Go to https://claude.ai
2. Start a new conversation
3. Paste the prompt from the **[PASTE INTO NEW CHAT]** section below

---

## [PASTE INTO NEW CHAT] START HERE

You're evaluating a music recommender system that scores songs based on user preferences and returns ranked recommendations.

### The Scoring Algorithm
1. **Genre Matching**: +2.0 if song genre matches favorite genre
2. **Mood Matching**: +1.5 if song mood matches favorite mood
3. **Numerical Features** (energy, valence, danceability):
   - If within tolerance band: `weight × 8.0` points
   - If outside tolerance band: `weight × 8.0 × 0.5` points
4. **Acousticness Bonus**: If user likes acoustic AND acousticness > 0.7, add acoustic_preference_strength points
5. **Hard Filter**: Songs with negative genres are excluded entirely

### Core Implementation Files

**src/recommender.py - The two main functions:**
```python
def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a single song against user preferences, returning (score, reasons)."""

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str, List[str]]]:
    """Recommend top k songs ranked by score, filtering negative genres."""
```

**src/test_profiles.py - Three baseline profiles:**
- HIGH_ENERGY_POP: pop, happy, high energy (0.85), high valence (0.85)
- CHILL_LOFI: lofi, calm, low energy (0.30), moderate valence (0.55), acoustic bonus
- DEEP_INTENSE_ROCK: rock, melancholic, high energy (0.75), low valence (0.35)

**src/adversarial_profiles.py - Eight edge-case profiles** (see file for details)

### Your Task

Analyze the scoring algorithm and user profiles to identify:

1. **Edge Cases**: Scenarios where the algorithm produces unexpected results
   - Example: CONFLICTING_EMOTIONS has energy=0.90 but valence=0.20 (sad mood)
   
2. **Potential Bugs**:
   - Are tolerance bands handled correctly?
   - What happens with extreme feature weights?
   - Does the hard genre filter work as expected?
   - Can feature weights sum to zero?

3. **Robustness Issues**:
   - Can contradictory preferences "trick" the algorithm?
   - Are rankings stable or arbitrary in edge cases?
   - What happens when negative genres eliminate most songs?

4. **Improvement Suggestions**:
   - Should conflicting preferences be detected and warned?
   - Should feature weights be normalized?
   - Should there be guard rails for edge cases?
   - Should the algorithm explain why a profile is problematic?

### Questions to Answer

For the adversarial profiles, specifically evaluate:

1. **PERFECTIONIST** (tolerance 0.05): Will it return k songs, or fewer?
2. **INDIFFERENT** (tolerance 0.40): Will all songs score nearly the same?
3. **ENERGY_OBSESSED** (all weights zero): How does it rank when no features matter?
4. **PICKY_EATER** (10+ negative genres): Can it return k songs from remaining pool?
5. **CONFLICTING_EMOTIONS**: Is the high-energy + melancholic combo handled sensibly?
6. **ACOUSTIC_PARADOX**: Does the acoustic bonus conflict with high-energy targets?

### What I'm Looking For

Please provide:
- **Analysis**: What each edge case reveals about the system
- **Verdict**: Is the current behavior acceptable, or is it a bug?
- **Recommendations**: How to fix or improve the algorithm
- **Priority**: Which issues are most critical to address?

---

## After the Evaluation

Once you have feedback from the evaluation chat:

1. **Document findings** in a new file or update existing docs
2. **Implement fixes** if critical bugs are found
3. **Add validation** to detect impossible profiles
4. **Write unit tests** using the adversarial profiles

---

## Quick Start to Test Locally

You can also test the profiles locally by modifying `src/main.py`:

```python
from test_profiles import HIGH_ENERGY_POP, CHILL_LOFI, DEEP_INTENSE_ROCK
from adversarial_profiles import CONFLICTING_EMOTIONS, PERFECTIONIST, ...

# Change this line in main():
user_prefs = CONFLICTING_EMOTIONS  # Test different profile
```

Then run: `python src/main.py`

---

## Files to Reference
- `SYSTEM_EVALUATION_PROMPT.md` - Full evaluation framework
- `src/test_profiles.py` - Three baseline profiles
- `src/adversarial_profiles.py` - Eight adversarial profiles with explanations
- `src/recommender.py` - Implementation to review
- `src/main.py` - CLI interface
