"""
Standalone evaluation harness for the Music Recommender.

Distinct from tests/test_adversarial.py and tests/test_recommender.py (which are
pytest regression tests meant for CI/dev-loop use): this script is meant to be run
directly to get a human-readable pass/fail report of the system's behavior across
every baseline and adversarial profile, without needing pytest installed.

Run with: python -m src.evaluate
"""

import logging
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

logging.basicConfig(level=logging.WARNING, format="%(levelname)s:%(name)s:%(message)s")

from src.adversarial_profiles import (
    ALL_ADVERSARIAL_PROFILES,
    ACOUSTIC_PARADOX,
    CONFLICTING_EMOTIONS,
    NO_FEATURES,
    PERFECTIONIST,
)
from src.recommender import load_songs, recommend_songs
from src.test_profiles import ALL_PROFILES, HIGH_ENERGY_POP


@dataclass
class Check:
    name: str
    profile: Dict
    predicate: Callable[["EvalRun"], bool]
    description: str


@dataclass
class EvalRun:
    items: List
    warnings: List[str]


def _run(profile: Dict, catalog: List[Dict], k: int = 5) -> EvalRun:
    result = recommend_songs(profile, catalog, k=k)
    return EvalRun(items=result.items, warnings=result.warnings)


def _never_crashes_and_bounded(run: EvalRun) -> bool:
    if not (0 <= len(run.items) <= 5):
        return False
    for _, score, explanation, reasons in run.items:
        if not (score >= 0.0 and score == score):  # score == score rules out NaN
            return False
        if not isinstance(explanation, str) or not reasons:
            return False
    return True


def _has_warning_containing(*substrings: str) -> Callable[[EvalRun], bool]:
    def check(run: EvalRun) -> bool:
        return all(any(s in w for w in run.warnings) for s in substrings)
    return check


def _returns_k(k: int) -> Callable[[EvalRun], bool]:
    return lambda run: len(run.items) == k


def _top_result_matches_genre_and_mood(run: EvalRun) -> bool:
    if not run.items:
        return False
    song = run.items[0][0]
    return song["genre"] == HIGH_ENERGY_POP["favorite_genre"] and song["mood"] == HIGH_ENERGY_POP["favorite_mood"]


CHECKS: List[Check] = [
    # Baseline profiles: should always return a full, well-formed ranking.
    *[
        Check(
            name=f"baseline:{profile['profile_name']}",
            profile=profile,
            predicate=_returns_k(5),
            description="baseline profile returns 5 ranked recommendations",
        )
        for profile in ALL_PROFILES
    ],
    Check(
        name="baseline:HIGH_ENERGY_POP top match",
        profile=HIGH_ENERGY_POP,
        predicate=_top_result_matches_genre_and_mood,
        description="top result for a pop/happy profile is itself pop and happy",
    ),
    # Adversarial profiles: should never crash, and known cases should trigger
    # the guardrail warning they were designed to expose.
    *[
        Check(
            name=f"adversarial:{profile['profile_name']}",
            profile=profile,
            predicate=_never_crashes_and_bounded,
            description="adversarial profile never crashes, scores stay finite/non-negative",
        )
        for profile in ALL_ADVERSARIAL_PROFILES
    ],
    Check(
        name="adversarial:PERFECTIONIST still returns 5",
        profile=PERFECTIONIST,
        predicate=_returns_k(5),
        description="0.05 tolerance bands on a 17-song catalog still yield 5 results",
    ),
    Check(
        name="adversarial:PERFECTIONIST guardrail fires",
        profile=PERFECTIONIST,
        predicate=_has_warning_containing("energy_tolerance", "valence_tolerance", "danceability_tolerance"),
        description="strict-tolerance warnings fire for all three numerical features",
    ),
    Check(
        name="adversarial:NO_FEATURES guardrail fires",
        profile=NO_FEATURES,
        predicate=_has_warning_containing("zero"),
        description="zero-weight warning fires when all feature weights are 0",
    ),
    Check(
        name="adversarial:CONFLICTING_EMOTIONS guardrail fires",
        profile=CONFLICTING_EMOTIONS,
        predicate=_has_warning_containing("target_valence"),
        description="high-energy/low-valence warning fires for the conflicting-emotions profile",
    ),
    Check(
        name="adversarial:ACOUSTIC_PARADOX guardrail fires",
        profile=ACOUSTIC_PARADOX,
        predicate=_has_warning_containing("likes_acoustic"),
        description="acoustic/energy paradox warning fires when both are set",
    ),
]


def main() -> None:
    catalog = load_songs("data/songs.csv")

    passed = 0
    failed = 0
    failures: List[str] = []

    print("\n" + "=" * 70)
    print("MUSIC RECOMMENDER -- EVALUATION HARNESS")
    print("=" * 70)

    for check in CHECKS:
        run = _run(check.profile, catalog)
        ok = check.predicate(run)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {check.name} -- {check.description}")
        if ok:
            passed += 1
        else:
            failed += 1
            failures.append(check.name)

    total = passed + failed
    print("\n" + "-" * 70)
    print(f"SUMMARY: {passed}/{total} checks passed ({passed / total:.0%} confidence)")
    if failures:
        print("Failed checks:")
        for name in failures:
            print(f"  - {name}")
    print("-" * 70 + "\n")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
