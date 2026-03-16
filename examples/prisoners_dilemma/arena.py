#!/usr/bin/env python3
"""
Prisoner's Dilemma arena — head-to-head evaluation harness.

Usage:
    uv run examples/prisoners_dilemma/arena.py v2 v1 --games 100 --rounds 200
    uv run examples/prisoners_dilemma/arena.py v2 v1 --record          # auto-record to db
    uv run examples/prisoners_dilemma/arena.py v2 v1 --trace --seed 42 # move-by-move replay
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
DB_DEFAULT = "examples/prisoners_dilemma/matches.json"


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


def play_game_traced(fn_a, fn_b, rounds: int, name_a: str, name_b: str):
    """Play one game with move-by-move output for diagnosis."""
    hist_a: list[bool] = []
    hist_b: list[bool] = []
    score_a, score_b = 0, 0
    noise_count_a, noise_count_b = 0, 0

    print(f"{'Rnd':>4}  {name_a:>6}  {name_b:>6}  {'Pay':>5}  {'Total':>10}  Note")
    print("─" * 55)

    for r in range(1, rounds + 1):
        intended_a = bool(fn_a(list(hist_a), list(hist_b)))
        intended_b = bool(fn_b(list(hist_b), list(hist_a)))

        move_a, move_b = intended_a, intended_b
        flipped_a = random.random() < NOISE
        flipped_b = random.random() < NOISE
        if flipped_a:
            move_a = not move_a
            noise_count_a += 1
        if flipped_b:
            move_b = not move_b
            noise_count_b += 1

        pa, pb = PAYOFFS[(move_a, move_b)]
        score_a += pa
        score_b += pb

        ma = "C" if move_a else "D"
        mb = "C" if move_b else "D"
        notes = []
        if flipped_a:
            notes.append(f"{name_a} noise")
        if flipped_b:
            notes.append(f"{name_b} noise")
        note = ", ".join(notes)

        print(f"{r:>4}  {ma:>6}  {mb:>6}  {pa},{pb:<2}  {score_a:>4}-{score_b:<4}  {note}")

        hist_a.append(move_a)
        hist_b.append(move_b)

    coop_a = sum(hist_a) / len(hist_a) * 100
    coop_b = sum(hist_b) / len(hist_b) * 100
    print("─" * 55)
    print(f"Final: {name_a}={score_a} ({score_a/rounds:.2f}/rnd, {coop_a:.0f}% coop, {noise_count_a} flips)")
    print(f"       {name_b}={score_b} ({score_b/rounds:.2f}/rnd, {coop_b:.0f}% coop, {noise_count_b} flips)")


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


def record_result(db_path: str, player_a: str, player_b: str, result: dict):
    """Record match result directly to the database."""
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from evolve import load_db, save_db

    db = load_db(db_path)
    match = {
        "a": player_a,
        "b": player_b,
        "wins_a": result["wins_a"],
        "wins_b": result["wins_b"],
        "mean_a": result["mean_a"],
        "mean_b": result["mean_b"],
    }
    db["matches"].append(match)
    for v in [player_a, player_b]:
        if v not in db["versions"]:
            db["versions"][v] = {}
    save_db(db, db_path)
    print(f"Recorded: {player_a} vs {player_b} = {result['wins_a']}W-{result['wins_b']}L → {db_path}")


def main():
    parser = argparse.ArgumentParser(description="Prisoner's Dilemma Arena")
    parser.add_argument("player_a", help="Strategy name (e.g. v2)")
    parser.add_argument("player_b", help="Strategy name (e.g. v1)")
    parser.add_argument("--games", type=int, default=100, help="Number of games (default: 100)")
    parser.add_argument("--rounds", type=int, default=200, help="Rounds per game (default: 200)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--record", action="store_true", help="Auto-record result to database")
    parser.add_argument("--db", default=DB_DEFAULT, help=f"Database path (default: {DB_DEFAULT})")
    parser.add_argument("--trace", action="store_true", help="Print move-by-move trace for 1 game")
    args = parser.parse_args()

    fn_a = load_strategy(args.player_a)
    fn_b = load_strategy(args.player_b)

    # Trace mode: single game with move-by-move output
    if args.trace:
        seed = args.seed if args.seed is not None else 42
        random.seed(seed)
        print(f"Trace: {args.player_a} vs {args.player_b} ({args.rounds} rounds, seed={seed})\n")
        play_game_traced(fn_a, fn_b, args.rounds, args.player_a, args.player_b)
        return

    # Normal mode: full match
    print(f"Arena: {args.player_a} vs {args.player_b}")
    print(f"  {args.games} games × {args.rounds} rounds, noise={NOISE:.0%}")
    print()

    result = run_match(fn_a, fn_b, args.games, args.rounds, args.seed)

    print(f"Results:")
    print(f"  {args.player_a}: {result['wins_a']} wins, mean {result['mean_a']:.4f}/round")
    print(f"  {args.player_b}: {result['wins_b']} wins, mean {result['mean_b']:.4f}/round")
    print(f"  Draws: {result['draws']}")
    print()

    if args.record:
        record_result(args.db, args.player_a, args.player_b, result)
    else:
        print(f"Record result:")
        print(
            f"  uv run tracker.py record {args.player_a} {args.player_b}"
            f" --wins {result['wins_a']} --losses {result['wins_b']}"
            f" --mean-a {result['mean_a']:.4f} --mean-b {result['mean_b']:.4f}"
            f" --db {args.db}"
        )


if __name__ == "__main__":
    main()
