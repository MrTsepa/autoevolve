"""
autoevolve — data layer and evaluation contract for self-play improvement.

The self-play *loop* lives in the skill (see SKILL.md): a coding agent is the
mutator and the loop driver. This file defines what the loop operates on — the
match database and the contract an arena must satisfy to be evaluated.

  - ``MatchResult`` / ``load_db`` / ``save_db`` / ``record`` — the match ledger.
  - ``Artifact`` / ``Evaluator`` — the typed expression of the arena contract:
    something with a version, and a way to compare two of them head-to-head.
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
    draws: int = 0
    mean_a: float | None = None
    mean_b: float | None = None
    note: str | None = None

    def to_dict(self) -> dict:
        d = {"a": self.a, "b": self.b, "wins_a": self.wins_a, "wins_b": self.wins_b}
        if self.draws:
            d["draws"] = self.draws
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
    """Compares two artifacts head-to-head and returns a MatchResult.

    This is the typed expression of the arena contract. In practice an arena
    conforms by exposing a command that prints the contract JSON:

        <eval-cmd> --a vN --b vM -n 100
        -> {"wins_a": int, "wins_b": int, "draws": int,
            "mean_a": float?, "mean_b": float?}
    """

    def evaluate(self, a: Artifact, b: Artifact, n_games: int) -> MatchResult: ...


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
    """Append a match result to the database (append-only)."""
    db["matches"].append(result.to_dict())
    for v in [result.a, result.b]:
        if v not in db["versions"]:
            db["versions"][v] = {}
    return db
