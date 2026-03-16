#!/usr/bin/env python3
"""
Prisoner's Dilemma arena — head-to-head evaluation harness.

Usage:
    uv run examples/prisoners_dilemma/arena.py v2 v1 --games 100 --rounds 200
"""

import argparse
import importlib.util
import random
import sys
from pathlib import Path

# ── Payoff matrix ────────────────────────────────────────────
# (row_payoff, col_payoff) indexed by (row_cooperates, col_cooperates)
PAYOFFS = {
    (True, True): (3, 3),
    (True, False): (0, 5),
    (False, True): (5, 0),
    (False, False): (1, 1),
}

NOISE = 0.05  # probability each move is flipped


def load_strategy(name: str):
    """Load strategy function from strategies/vN.py."""
    path = Path(__file__).parent / "strategies" / f"{name}.py"
    if not path.exists():
        print(f"Error: strategy file not found: {path}", file=sys.stderr)
        sys.exit(1)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "strategy"):
        print(f"Error: {path} has no 'strategy' function", file=sys.stderr)
        sys.exit(1)
    return mod.strategy


def play_round(fn_a, fn_b, hist_a, hist_b):
    """Play one round. Returns (move_a, move_b) after applying noise."""
    move_a = fn_a(list(hist_a), list(hist_b))
    move_b = fn_b(list(hist_b), list(hist_a))

    # Apply noise — 5% chance each move is flipped
    if random.random() < NOISE:
        move_a = not move_a
    if random.random() < NOISE:
        move_b = not move_b

    return bool(move_a), bool(move_b)


def play_game(fn_a, fn_b, rounds: int) -> tuple[int, int]:
    """Play one game of `rounds` rounds. Returns (score_a, score_b)."""
    hist_a: list[bool] = []
    hist_b: list[bool] = []
    score_a, score_b = 0, 0

    for _ in range(rounds):
        move_a, move_b = play_round(fn_a, fn_b, hist_a, hist_b)
        pa, pb = PAYOFFS[(move_a, move_b)]
        score_a += pa
        score_b += pb
        hist_a.append(move_a)
        hist_b.append(move_b)

    return score_a, score_b


def run_match(fn_a, fn_b, games: int, rounds: int, seed: int | None = None):
    """Run a full match of `games` games. Returns results dict."""
    if seed is not None:
        random.seed(seed)

    wins_a, wins_b, draws = 0, 0, 0
    total_a, total_b = 0, 0

    for _ in range(games):
        sa, sb = play_game(fn_a, fn_b, rounds)
        total_a += sa
        total_b += sb
        if sa > sb:
            wins_a += 1
        elif sb > sa:
            wins_b += 1
        else:
            draws += 1

    mean_a = total_a / (games * rounds)
    mean_b = total_b / (games * rounds)

    return {
        "wins_a": wins_a,
        "wins_b": wins_b,
        "draws": draws,
        "mean_a": round(mean_a, 4),
        "mean_b": round(mean_b, 4),
        "total_a": total_a,
        "total_b": total_b,
        "games": games,
        "rounds": rounds,
    }


def main():
    parser = argparse.ArgumentParser(description="Prisoner's Dilemma Arena")
    parser.add_argument("player_a", help="Strategy name (e.g. v2)")
    parser.add_argument("player_b", help="Strategy name (e.g. v1)")
    parser.add_argument("--games", type=int, default=100, help="Number of games (default: 100)")
    parser.add_argument("--rounds", type=int, default=200, help="Rounds per game (default: 200)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    fn_a = load_strategy(args.player_a)
    fn_b = load_strategy(args.player_b)

    print(f"Arena: {args.player_a} vs {args.player_b}")
    print(f"  {args.games} games × {args.rounds} rounds, noise={NOISE:.0%}")
    print()

    result = run_match(fn_a, fn_b, args.games, args.rounds, args.seed)

    print(f"Results:")
    print(f"  {args.player_a}: {result['wins_a']} wins, mean {result['mean_a']:.4f}/round")
    print(f"  {args.player_b}: {result['wins_b']} wins, mean {result['mean_b']:.4f}/round")
    print(f"  Draws: {result['draws']}")
    print()

    db_path = "examples/prisoners_dilemma/matches.json"
    print(f"Record result:")
    print(
        f"  uv run tracker.py --db {db_path} record {args.player_a} {args.player_b}"
        f" --wins {result['wins_a']} --losses {result['wins_b']}"
        f" --mean-a {result['mean_a']:.4f} --mean-b {result['mean_b']:.4f}"
    )


if __name__ == "__main__":
    main()
