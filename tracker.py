#!/usr/bin/env python3
"""
autoevolve tracker — CLI for managing evolution experiments.

Usage:
    python tracker.py record v3 v1 --wins 62 --losses 38
    python tracker.py leaderboard
    python tracker.py matrix
    python tracker.py plot
    python tracker.py validate
    python tracker.py suggest v5
"""

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from evolve import load_db, save_db
from ratings import compute_ratings, compute_stats, pareto_front


# ── Defaults ────────────────────────────────────────────────

DB_PATH = Path("matches.json")
PLOT_PATH = Path("progress.png")


# ── Display helpers ─────────────────────────────────────────


def _dims(ratings, stats):
    return {
        v: [ratings[v], stats.get(v, {}).get("margin", 0), stats.get(v, {}).get("win_rate", 50)]
        for v in ratings
    }


def show_leaderboard(db):
    ratings, _ = compute_ratings(db)
    stats = compute_stats(db)
    if not ratings:
        print("No matches recorded yet.")
        return

    sorted_v = sorted(ratings, key=ratings.get, reverse=True)
    front = pareto_front(sorted_v, _dims(ratings, stats))

    print(f"\n{'':>3} {'Version':<12} {'Elo':>6} {'WR%':>6} {'Margin':>8} {'Games':>6} {'Pareto':>7}")
    print("\u2014" * 52)
    for i, v in enumerate(sorted_v):
        s = stats.get(v, {"win_rate": 50, "margin": 0, "games": 0})
        p = " *" if v in front else ""
        print(
            f"{i+1:>3} {v:<12} {ratings[v]:>6.0f} {s['win_rate']:>5.1f}% "
            f"{s['margin']:>+7.1f} {s['games']:>6}{p}"
        )


# ── Commands ────────────────────────────────────────────────


def cmd_record(args):
    db = load_db(args.db)
    match = {"a": args.version_a, "b": args.version_b, "wins_a": args.wins, "wins_b": args.losses}
    if args.mean_a is not None:
        match["mean_a"] = args.mean_a
    if args.mean_b is not None:
        match["mean_b"] = args.mean_b
    if args.note:
        match["note"] = args.note
    db["matches"].append(match)
    for v in [args.version_a, args.version_b]:
        if v not in db["versions"]:
            db["versions"][v] = {}
    save_db(db, args.db)
    print(f"Recorded: {args.version_a} vs {args.version_b} = {args.wins}W-{args.losses}L")
    show_leaderboard(db)


def cmd_leaderboard(args):
    show_leaderboard(load_db(args.db))


def cmd_pareto(args):
    db = load_db(args.db)
    ratings, _ = compute_ratings(db)
    stats = compute_stats(db)
    if not ratings:
        print("No matches recorded yet.")
        return

    front = pareto_front(list(ratings.keys()), _dims(ratings, stats))

    print("Pareto front (non-dominated across Elo, margin, win rate):")
    print(f"\n{'Version':<12} {'Elo':>6} {'Margin':>8} {'WR%':>6}")
    print("\u2014" * 36)
    for v in sorted(front, key=lambda x: ratings[x], reverse=True):
        s = stats.get(v, {"win_rate": 50, "margin": 0})
        print(f"{v:<12} {ratings[v]:>6.0f} {s['margin']:>+7.1f} {s['win_rate']:>5.1f}%")


def cmd_matrix(args):
    db = load_db(args.db)
    h2h = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for m in db["matches"]:
        a, b = m["a"], m["b"]
        h2h[a][b][0] += m["wins_a"]
        h2h[a][b][1] += m["wins_b"]
        h2h[b][a][0] += m["wins_b"]
        h2h[b][a][1] += m["wins_a"]

    versions = sorted(set(v for m in db["matches"] for v in [m["a"], m["b"]]))
    if not versions:
        print("No matches recorded.")
        return

    col_w = 8
    print(f"{'':>{col_w}}", end="")
    for v in versions:
        print(f"{v:>{col_w}}", end="")
    print()
    for a in versions:
        print(f"{a:>{col_w}}", end="")
        for b in versions:
            dash = "\u2014"
            if a == b:
                print(f"{dash:>{col_w}}", end="")
            elif h2h[a][b][0] + h2h[a][b][1] > 0:
                w, l = h2h[a][b]
                wr = w / (w + l) * 100
                print(f"{wr:>{col_w - 1}.0f}%", end="")
            else:
                print(f"{'':>{col_w}}", end="")
        print()


def cmd_plot(args):
    """Generate progress.png: Elo bars, Elo progression, h2h heatmap, Pareto scatter."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    db = load_db(args.db)
    ratings, _ = compute_ratings(db)
    stats = compute_stats(db)
    if not ratings:
        print("No matches recorded yet.")
        return

    plot_path = Path(args.db).parent / "progress.png"
    all_v = sorted(ratings, key=ratings.get, reverse=True)
    front = pareto_front(all_v, _dims(ratings, stats))
    top = all_v[:15]

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Evolution Progress", fontsize=14, fontweight="bold")

    # 1. Elo bar chart
    ax = axes[0, 0]
    colors = ["#2ecc71" if v in front else "#3498db" for v in top]
    elos = [ratings[v] for v in top]
    ax.barh(range(len(top)), elos, color=colors)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top, fontsize=9)
    ax.set_xlabel("Elo Rating")
    ax.set_title("Top 15 (green = Pareto)")
    ax.invert_yaxis()
    ax.set_xlim(max(0, min(elos) - 50), max(elos) + 30)
    for i, v in enumerate(top):
        ax.text(ratings[v] + 1, i, f"{ratings[v]:.0f}", va="center", fontsize=8)

    # 2. Elo over time (cumulative recomputation)
    ax = axes[0, 1]
    history = defaultdict(list)
    for idx in range(1, len(db["matches"]) + 1):
        partial = {"matches": db["matches"][:idx], "versions": db["versions"]}
        pr, _ = compute_ratings(partial)
        for v, elo in pr.items():
            history[v].append((idx - 1, elo))
    for v in top:
        if v in history:
            xs, ys = zip(*history[v])
            style = "-" if v in front else "--"
            ax.plot(xs, ys, style, label=v, linewidth=1.5 if v in front else 1.0)
    ax.set_xlabel("Match #")
    ax.set_ylabel("Elo")
    ax.set_title("Rating Progression")
    ax.legend(fontsize=7, loc="best")

    # 3. Head-to-head heatmap
    ax = axes[1, 0]
    h2h = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for m in db["matches"]:
        a, b = m["a"], m["b"]
        h2h[a][b][0] += m["wins_a"]
        h2h[a][b][1] += m["wins_b"]
        h2h[b][a][0] += m["wins_b"]
        h2h[b][a][1] += m["wins_a"]
    n = len(top)
    matrix = np.full((n, n), np.nan)
    for i, a in enumerate(top):
        for j, b in enumerate(top):
            if i != j and h2h[a][b][0] + h2h[a][b][1] > 0:
                w, l = h2h[a][b]
                matrix[i, j] = w / (w + l) * 100
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=20, vmax=80, aspect="auto")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(top, fontsize=7, rotation=45, ha="right")
    ax.set_yticklabels(top, fontsize=7)
    ax.set_title("Head-to-Head Win Rate %")
    for i in range(n):
        for j in range(n):
            if not np.isnan(matrix[i, j]):
                color = "white" if matrix[i, j] < 35 or matrix[i, j] > 65 else "black"
                ax.text(
                    j, i, f"{matrix[i, j]:.0f}", ha="center", va="center", fontsize=7, color=color
                )
    fig.colorbar(im, ax=ax, shrink=0.8)

    # 4. Pareto scatter
    ax = axes[1, 1]
    for v in top:
        s = stats.get(v, {"win_rate": 50, "margin": 0, "games": 0})
        color = "#2ecc71" if v in front else "#95a5a6"
        size = max(20, min(400, s["games"]))
        ax.scatter(
            s["margin"], ratings[v], c=color, s=size, edgecolors="black", linewidth=0.5, zorder=3
        )
        ax.annotate(
            v, (s["margin"], ratings[v]), fontsize=7, textcoords="offset points", xytext=(5, 5)
        )
    ax.set_xlabel("Score Margin")
    ax.set_ylabel("Elo Rating")
    ax.set_title("Pareto: Elo vs Margin")
    ax.axhline(y=1500, color="gray", linestyle=":", alpha=0.5)
    ax.axvline(x=0, color="gray", linestyle=":", alpha=0.5)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    print(f"Saved: {plot_path}")


def cmd_validate(args):
    """Assess Elo reliability: prediction accuracy + bootstrap confidence intervals."""
    import random as pyrandom

    db = load_db(args.db)
    ratings, match_counts = compute_ratings(db)
    if not ratings:
        print("No matches recorded yet.")
        return

    pair_data = defaultdict(lambda: [0, 0])
    for m in db["matches"]:
        a, b = m["a"], m["b"]
        if a not in ratings or b not in ratings:
            continue
        key = (min(a, b), max(a, b))
        if a < b:
            pair_data[key][0] += m["wins_a"]
            pair_data[key][1] += m["wins_b"]
        else:
            pair_data[key][1] += m["wins_a"]
            pair_data[key][0] += m["wins_b"]

    correct, total = 0, 0
    residuals = []
    for (a, b), (wa, wb) in pair_data.items():
        n = wa + wb
        if n == 0:
            continue
        elo_diff = ratings[a] - ratings[b]
        pred_wr = 1 / (1 + 10 ** (-elo_diff / 400))
        actual_wr = wa / n
        pred_winner = a if pred_wr >= 0.5 else b
        actual_winner = a if wa > wb else b if wb > wa else None
        if actual_winner and pred_winner == actual_winner:
            correct += 1
        total += 1
        residuals.append((a, b, n, pred_wr * 100, actual_wr * 100))

    print("=== Prediction Accuracy ===")
    if total:
        print(f"  Correct: {correct}/{total} ({correct / total * 100:.1f}%)")
    residuals.sort(key=lambda x: abs(x[3] - x[4]), reverse=True)
    print(f"\n  Biggest misses:")
    for a, b, n, pred, actual in residuals[:5]:
        print(f"    {a:>6} vs {b:<6}: pred {pred:5.1f}%, actual {actual:5.1f}% ({n} games)")

    # Bootstrap CI
    print(f"\n=== Bootstrap Confidence Intervals (100 resamples) ===")
    bootstrap = defaultdict(list)
    for _ in range(100):
        resampled = [pyrandom.choice(db["matches"]) for _ in range(len(db["matches"]))]
        br, _ = compute_ratings({"matches": resampled, "versions": db["versions"]})
        for v, r in br.items():
            bootstrap[v].append(r)

    sorted_v = sorted(ratings, key=ratings.get, reverse=True)[:15]
    print(f"\n  {'Version':<10} {'Elo':>6} {'95% CI':>16} {'Width':>7}")
    print("  " + "\u2014" * 42)
    for v in sorted_v:
        if v not in bootstrap or len(bootstrap[v]) < 10:
            continue
        bs = sorted(bootstrap[v])
        lo = bs[max(0, int(len(bs) * 0.025))]
        hi = bs[min(len(bs) - 1, int(len(bs) * 0.975))]
        print(f"  {v:<10} {ratings[v]:>6.0f} [{lo:>6.0f} - {hi:>5.0f}] {hi - lo:>6.0f}")


def cmd_suggest(args):
    """Suggest opponent using information-theoretic scoring: p*(1-p) / sqrt(games+1)."""
    db = load_db(args.db)
    ratings, _ = compute_ratings(db)
    if args.version not in ratings:
        print(f"{args.version} not in database. Available: {', '.join(sorted(ratings))}")
        return

    h2h_games = defaultdict(int)
    for m in db["matches"]:
        if m["a"] == args.version:
            h2h_games[m["b"]] += m["wins_a"] + m["wins_b"]
        elif m["b"] == args.version:
            h2h_games[m["a"]] += m["wins_a"] + m["wins_b"]

    scored = []
    for v in ratings:
        if v == args.version:
            continue
        elo_diff = ratings[args.version] - ratings[v]
        p = 1 / (1 + 10 ** (-elo_diff / 400))
        info = p * (1 - p) / math.sqrt(h2h_games.get(v, 0) + 1)
        scored.append((info, v))
    scored.sort(reverse=True)

    print(f"Suggested opponents for {args.version} (Elo {ratings[args.version]:.0f}):")
    for info, v in scored[:5]:
        games = h2h_games.get(v, 0)
        print(f"  {v:<12} Elo {ratings[v]:>6.0f}  ({games} h2h games, info {info:.4f})")


# ── CLI ─────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="autoevolve tracker")
    parser.add_argument("--db", default="matches.json", help="Path to matches.json")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("record", help="Record a match result")
    p.add_argument("version_a")
    p.add_argument("version_b")
    p.add_argument("--wins", type=int, required=True)
    p.add_argument("--losses", type=int, required=True)
    p.add_argument("--mean-a", type=float, default=None)
    p.add_argument("--mean-b", type=float, default=None)
    p.add_argument("--note", default=None)

    sub.add_parser("leaderboard", help="Show Elo leaderboard")
    sub.add_parser("pareto", help="Show Pareto front")
    sub.add_parser("matrix", help="Show head-to-head matrix")
    sub.add_parser("plot", help="Generate progress.png (requires matplotlib)")
    sub.add_parser("validate", help="Assess rating reliability")

    p = sub.add_parser("suggest", help="Suggest next opponent")
    p.add_argument("version")

    commands = {
        "record": cmd_record,
        "leaderboard": cmd_leaderboard,
        "pareto": cmd_pareto,
        "matrix": cmd_matrix,
        "plot": cmd_plot,
        "validate": cmd_validate,
        "suggest": cmd_suggest,
    }

    args = parser.parse_args()
    func = commands.get(args.cmd)
    if func:
        func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
