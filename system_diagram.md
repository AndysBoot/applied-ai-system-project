# System Diagram — Music Recommender Applied AI System

This diagram reflects the actual architecture: a rule-based recommendation engine wrapped by two
AI-powered reliability components (guardrails and smart explanations), plus an automated adversarial
test suite that validates robustness across edge cases.

```mermaid
flowchart TD
    A1["User profile<br/>favorite_genre, mood, energy/valence/dance targets,<br/>tolerance bands, feature_weights, negative_genres"]
    A2["Song catalog<br/>data/songs.db (SQLite)<br/>populated via scripts/manage_songs.py<br/>from the MusicBrainz API (real songs)"]
    A3["Adversarial profiles<br/>src/adversarial_profiles.py<br/>(8 edge-case profiles)<br/>for stress-testing"]
    A4["data/songs.csv<br/>fixed fabricated catalog --<br/>used ONLY by tests/ for<br/>reproducible regression checks,<br/>never by the live app"]

    subgraph GUARD["AI Reliability: Guardrail Layer — src/guardrails.py"]
        B1["validate_profile()<br/>(pattern-matching checker)"]
        B2{"Detects contradictions:<br/>zero weights / strict tolerance /<br/>energy-mood mismatch /<br/>acoustic-energy paradox /<br/>negative-genre wipeout"}
    end

    subgraph CORE["Core Recommendation Engine — src/recommender.py"]
        C1["load_songs_smart()<br/>reads data/songs.db only --<br/>errors instead of silently<br/>using the fabricated songs.csv"]
        C2["score_song()<br/>smoothed tolerance scoring<br/>genre + mood + weighted features"]
        C3["recommend_songs()<br/>rank by score, filter negatives,<br/>fallback if pool empty"]
    end

    subgraph EXPLAIN["AI Reliability: Smart Template-Based Explanations — src/explain.py"]
        D1["Analyze scoring pattern<br/>identify what matched:<br/>genre, mood, energy,<br/>valence, danceability, acoustic"]
        D2["Convert numeric attributes<br/>to descriptive phrases<br/>e.g. 0.85 energy → 'energetic'"]
        D3["Select contextual template<br/>based on match pattern<br/>and song characteristics"]
        D4["Generate natural-language<br/>explanation grounded in<br/>actual song data"]
    end

    subgraph OUT["Output — src/main.py CLI & app.py Streamlit UI"]
        E1["Ranked recommendations<br/>+ scores/12.0"]
        E2["Why-matched reasons<br/>(deterministic scoring breakdown)"]
        E3["AI-generated explanation<br/>(smart templates)"]
        E4["Guardrail warnings<br/>(logged + printed)"]
    end

    subgraph TEST["AI Reliability: Automated Testing — tests/"]
        F1["test_recommender.py<br/>3 baseline profiles<br/>(typical use cases)"]
        F2["test_adversarial.py<br/>8 adversarial profiles<br/>(edge cases that expose bugs)"]
        F3["All assertions validate:<br/>no crash, bounded scores,<br/>expected warnings fired,<br/>k recommendations returned"]
    end

    subgraph HUMAN["Human-in-the-Loop Feedback"]
        G1["Developer reviews test results<br/>+ model_card.md limitations"]
        G2["Manual review of guardrail<br/>warnings + explanations"]
        G3["Adjust weights, tolerances,<br/>or guardrail thresholds<br/>based on findings"]
    end

    A1 --> B1
    A2 --> C1
    B1 --> B2
    B2 -->|warnings logged| C3
    C1 --> C2 --> C3
    C3 --> D1
    D1 --> D2 --> D3 --> D4
    D4 --> E3
    C3 --> E1
    C3 --> E2
    B2 --> E4

    A3 --> F2
    A4 --> F1
    C3 --> F3
    F1 --> F3
    F2 --> F3
    F3 -->|assertions pass| E1
    F3 -->|assertions fail| G3

    E3 --> G2
    E4 --> G1
    G1 --> G3
    G3 -.feedback loop.-> B1
```

## Component key

| Component | Role |
|---|---|
| **Guardrail layer** (`guardrails.py`) | Validates a user profile *before* scoring — catches contradictions and degenerate inputs (zero weights, overly strict tolerance, energy/mood mismatches, genre filters that would empty the catalog) and logs warnings instead of crashing. |
| **Recommendation engine** (`recommender.py`) | Loads the catalog, scores each song against the profile with smoothed tolerance bands, ranks and filters, and falls back to an unfiltered pool if a hard filter would return nothing. |
| **Smart template-based explanation layer** (`explain.py`) | Analyzes each recommended song's scoring breakdown to identify which factors matched (genre, mood, energy, valence, danceability, acoustic), converts numeric attributes to descriptive phrases, and selects a contextual natural-language template grounded only in that song's actual data — no external API calls, fully deterministic. |
| **Automated testing** (`tests/`) | `test_adversarial.py` runs all 8 adversarial profiles through the full pipeline on every `pytest` run, asserting the guardrails and scoring behave correctly under edge cases — this is the system checking itself, continuously. |
| **Human-in-the-loop** | A developer reads guardrail warnings and test failures (`model_card.md` documents this history), spot-checks AI-generated explanations for hallucination or tone issues, and tunes thresholds/weights based on what the automated layer surfaces. Humans supervise and adjust; they don't approve every individual recommendation. |

## Data flow summary

**Input** → user profile + song catalog (and, in testing, the 8 adversarial profiles) →
**Guardrail check** (warns on bad input, never blocks) → **Scoring/ranking** → **Template
selection** grounded in each top result's own scoring data → **Generation** of a
natural-language explanation → **Output** to the CLI (recommendations, reasons, AI explanation,
warnings). In parallel, the **test suite** exercises this same pipeline against known-hard inputs
on every run, and its pass/fail result plus the logged warnings are what a **human** reviews to
decide whether to adjust the system.
