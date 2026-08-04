# System Diagram — Music Recommender Applied AI System

This diagram reflects the planned architecture: a rule-based recommendation engine wrapped by a
guardrail/validation layer, a RAG explanation layer, and an automated adversarial test suite that
checks the whole pipeline.

```mermaid
flowchart TD
    A1["User profile<br/>favorite_genre, mood, energy/valence/dance targets,<br/>tolerance bands, feature_weights, negative_genres"]
    A2["Song catalog<br/>data/songs.db (SQLite)<br/>populated via scripts/manage_songs.py<br/>from the MusicBrainz API (real songs)"]
    A3["Adversarial profiles<br/>src/adversarial_profiles.py<br/>(8 edge-case profiles)"]
    A4["data/songs.csv<br/>fixed fabricated catalog --<br/>used ONLY by tests/ for<br/>reproducible regression checks,<br/>never by the live app"]

    subgraph GUARD["Guardrail layer — src/guardrails.py"]
        B1["validate_profile()"]
        B2{"Contradiction or<br/>degenerate input?<br/>zero weights / strict tolerance /<br/>energy-mood mismatch /<br/>negative-genre wipeout"}
    end

    subgraph CORE["Recommendation engine — src/recommender.py"]
        C1["load_songs_smart()<br/>reads data/songs.db only --<br/>errors instead of silently<br/>using the fabricated songs.csv"]
        C2["score_song()<br/>smoothed tolerance scoring"]
        C3["recommend_songs()<br/>rank, filter, fallback if pool empty"]
    end

    subgraph RAG["RAG explanation layer — src/explain.py"]
        D1["Retriever<br/>pull each recommended song's full record +<br/>genre/mood-matched comparison songs"]
        D2{"ANTHROPIC_API_KEY set<br/>and call succeeds?"}
        D3["Single batched Claude call<br/>returns one grounded explanation<br/>per recommended song (not per-call)"]
        D4["Fallback: deterministic<br/>templated reason string"]
    end

    subgraph OUT["Output — src/main.py CLI"]
        E1["Ranked recommendations + scores"]
        E2["Why-matched reasons (deterministic)"]
        E3["AI explanation (RAG or fallback)"]
        E4["Guardrail warnings (logged + printed)"]
    end

    subgraph TEST["Automated testing — tests/"]
        F1["test_recommender.py<br/>baseline profile checks"]
        F2["test_adversarial.py<br/>runs all 8 adversarial profiles"]
        F3{"Assertions pass?<br/>no crash, bounded scores,<br/>expected warnings fired"}
    end

    subgraph HUMAN["Human-in-the-loop"]
        G1["Developer reviews logs<br/>+ model_card.md findings"]
        G2["Manual spot-check of AI<br/>explanations for accuracy/tone"]
        G3["Adjust weights, tolerance,<br/>or guardrail thresholds"]
    end

    A1 --> B1
    A2 --> C1
    B1 --> B2
    B2 -->|warnings logged| C3
    C1 --> C2 --> C3
    C3 --> D1
    D1 --> D2
    D2 -->|yes| D3
    D2 -->|no / error| D4
    D3 --> E3
    D4 --> E3
    C3 --> E1
    C3 --> E2
    B2 --> E4

    A3 --> F2
    A4 --> F1
    C3 --> F3
    F1 --> F3
    F2 --> F3
    F3 -->|fail| G3
    F3 -->|pass| E1

    E3 --> G2
    E4 --> G1
    G1 --> G3
    G3 -.feedback.-> B1
```

## Component key

| Component | Role |
|---|---|
| **Guardrail layer** (`guardrails.py`) | Validates a user profile *before* scoring — catches contradictions and degenerate inputs (zero weights, overly strict tolerance, energy/mood mismatches, genre filters that would empty the catalog) and logs warnings instead of crashing. |
| **Recommendation engine** (`recommender.py`) | Loads the catalog, scores each song against the profile with smoothed tolerance bands, ranks and filters, and falls back to an unfiltered pool if a hard filter would return nothing. |
| **RAG explanation layer** (`explain.py`) | Retrieves each recommended song's full attributes plus similar catalog songs, then makes ONE batched Claude call for the whole result set (not one call per song) asking it to generate short explanations grounded only in that retrieved data — never invents facts. Falls back to the deterministic reason string per song if no API key is set or the call fails/doesn't parse. |
| **Automated testing** (`tests/`) | `test_adversarial.py` runs all 8 adversarial profiles through the full pipeline on every `pytest` run, asserting the guardrails and scoring behave correctly under edge cases — this is the system checking itself, continuously. |
| **Human-in-the-loop** | A developer reads guardrail warnings and test failures (`model_card.md` documents this history), spot-checks AI-generated explanations for hallucination or tone issues, and tunes thresholds/weights based on what the automated layer surfaces. Humans supervise and adjust; they don't approve every individual recommendation. |

## Data flow summary

**Input** → user profile + song catalog (and, in testing, the 8 adversarial profiles) →
**Guardrail check** (warns on bad input, never blocks) → **Scoring/ranking** → **Retrieval** of
grounding data for the top results → **Generation** of a natural-language explanation (or
deterministic fallback) → **Output** to the CLI (recommendations, reasons, AI explanation,
warnings). In parallel, the **test suite** exercises this same pipeline against known-hard inputs
on every run, and its pass/fail result plus the logged warnings are what a **human** reviews to
decide whether to adjust the system.
