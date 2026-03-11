"""
autoevolve — GEPA loop for automated iterative improvement.

Generate -> Evaluate -> Promote -> Archive

A coding agent creates candidate variants of an artifact (a bot, prompt, strategy,
or model config), evaluates them through head-to-head comparison, promotes the
winners based on Elo ratings, and archives everything for traceability.

This file defines the core loop and its building blocks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


# ── Data ────────────────────────────────────────────────────


@dataclass
class MatchResult:
    """Outcome of evaluating artifact A vs artifact B."""

    a: str
    b: str
    wins_a: int
    wins_b: int
    mean_a: float | None = None
    mean_b: float | None = None
    note: str | None = None

    def to_dict(self) -> dict:
        d = {"a": self.a, "b": self.b, "wins_a": self.wins_a, "wins_b": self.wins_b}
        if self.mean_a is not None:
            d["mean_a"] = self.mean_a
        if self.mean_b is not None:
            d["mean_b"] = self.mean_b
        if self.note:
            d["note"] = self.note
        return d


# ── Protocols ───────────────────────────────────────────────


@runtime_checkable
class Artifact(Protocol):
    """Something that can be versioned and compared."""

    @property
    def version(self) -> str: ...


@runtime_checkable
class Evaluator(Protocol):
    """Compares two artifacts. Returns a MatchResult."""

    def evaluate(self, a: Artifact, b: Artifact, n_games: int) -> MatchResult: ...


@runtime_checkable
class Mutator(Protocol):
    """Creates a new candidate from a parent artifact."""

    def mutate(self, parent: Artifact) -> Artifact: ...


# ── Database ────────────────────────────────────────────────


def load_db(path: str | Path = "matches.json") -> dict:
    """Load match database from JSON file."""
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text())
    return {"matches": [], "versions": {}}


def save_db(db: dict, path: str | Path = "matches.json"):
    """Save match database to JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(db, indent=2) + "\n")


def record(db: dict, result: MatchResult) -> dict:
    """Append a match result to the database."""
    db["matches"].append(result.to_dict())
    for v in [result.a, result.b]:
        if v not in db["versions"]:
            db["versions"][v] = {}
    return db


# ── GEPA loop ───────────────────────────────────────────────


def evolve(
    seed: Artifact,
    mutator: Mutator,
    evaluator: Evaluator,
    *,
    db_path: str | Path = "matches.json",
    n_games: int = 100,
    n_candidates: int = 1,
    max_generations: int = 50,
    on_step: callable | None = None,
) -> dict:
    """
    Run the Generate-Evaluate-Promote-Archive loop.

    Each generation:
      1. Generate — mutator creates n_candidates variants from current best
      2. Evaluate — each candidate plays n_games against current best
      3. Promote — recompute ratings, crown new best if earned
      4. Archive — save DB, call on_step callback

    Returns the final database.
    """
    from ratings import compute_ratings

    db = load_db(db_path)
    best_version = seed.version

    for gen in range(max_generations):
        # GENERATE
        candidates = [mutator.mutate(seed) for _ in range(n_candidates)]

        # EVALUATE
        for candidate in candidates:
            result = evaluator.evaluate(candidate, seed, n_games)
            record(db, result)

        # PROMOTE
        save_db(db, db_path)
        ratings, _ = compute_ratings(db)
        if ratings:
            best_version = max(ratings, key=ratings.get)

        # ARCHIVE
        if on_step:
            on_step(gen=gen, best=best_version, ratings=ratings, db=db)

    return db
