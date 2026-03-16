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
import os
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


def show_leaderboard(db, min_opponents=3):
    ratings, _ = compute_ratings(db)
    stats = compute_stats(db)
    if not ratings:
        print("No matches recorded yet.")
        return

    sorted_v = sorted(ratings, key=ratings.get, reverse=True)
    front = pareto_front(sorted_v, _dims(ratings, stats))

    print(f"\n{'':>3} {'Version':<12} {'Elo':>6} {'WR%':>6} {'Margin':>8} {'Games':>6} {'Opp':>5} {'':>7}")
    print("\u2014" * 58)
    for i, v in enumerate(sorted_v):
        s = stats.get(v, {"win_rate": 50, "margin": 0, "games": 0, "opponents": 0})
        opp = s.get("opponents", 0)
        flags = ""
        if v in front and opp >= min_opponents:
            flags = " *"
        elif opp < min_opponents:
            flags = " ?"
        print(
            f"{i+1:>3} {v:<12} {ratings[v]:>6.0f} {s['win_rate']:>5.1f}% "
            f"{s['margin']:>+7.1f} {s['games']:>6} {opp:>4}{flags}"
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


def cmd_progress(args):
    """Generate progress.png — autoresearch-style scatter of Elo over version number."""
    import re

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    db = load_db(args.db)
    ratings, _ = compute_ratings(db)
    stats = compute_stats(db)
    if not ratings:
        print("No matches recorded yet.")
        return

    plot_path = Path(args.db).parent / "progress.png"

    # Sort versions by natural order (v1, v2, ... v10, v11, ...)
    def sort_key(v):
        m = re.match(r"v(\d+)", v)
        return (int(m.group(1)), v) if m else (float("inf"), v)

    all_v = sorted(ratings.keys(), key=sort_key)

    # Determine which versions are "kept" (were ever the best at time of creation)
    # Approximate: a version is "kept" if it's on the Pareto front or was ever #1
    dims = _dims(ratings, stats)
    front = pareto_front(all_v, dims)

    # Build running best
    running_best_elo = float("-inf")
    running_best_xs, running_best_ys = [], []
    xs, ys, kept = [], [], []
    for i, v in enumerate(all_v):
        elo = ratings[v]
        xs.append(i)
        ys.append(elo)
        is_kept = elo > running_best_elo
        kept.append(is_kept)
        if is_kept:
            running_best_elo = elo
            running_best_xs.append(i)
            running_best_ys.append(elo)

    # Extend running best line to the end
    if running_best_xs:
        running_best_xs.append(xs[-1])
        running_best_ys.append(running_best_ys[-1])

    n_kept = sum(kept)
    n_total = len(all_v)

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle(
        f"Evolution Progress: {n_total} Versions, {n_kept} Kept Improvements",
        fontsize=13,
        fontweight="bold",
    )

    # Discarded (gray)
    disc_xs = [x for x, k in zip(xs, kept) if not k]
    disc_ys = [y for y, k in zip(ys, kept) if not k]
    ax.scatter(disc_xs, disc_ys, c="#cccccc", s=40, zorder=2, label="Discarded")

    # Kept (green)
    kept_xs = [x for x, k in zip(xs, kept) if k]
    kept_ys = [y for y, k in zip(ys, kept) if k]
    ax.scatter(kept_xs, kept_ys, c="#2ecc71", s=60, zorder=3, label="Kept", edgecolors="white", linewidth=0.5)

    # Running best staircase
    ax.step(running_best_xs, running_best_ys, where="post", c="#2ecc71", linewidth=1.5, zorder=2, label="Running best")

    # Annotate kept versions
    for x, y, v, k in zip(xs, ys, all_v, kept):
        if k:
            ax.annotate(
                v, (x, y), fontsize=7, color="#333333",
                textcoords="offset points", xytext=(5, 5), rotation=30,
            )

    ax.set_xlabel("Version #")
    ax.set_ylabel("Elo Rating (higher is better)")
    ax.set_xticks(range(0, len(all_v), max(1, len(all_v) // 15)))
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    print(f"Saved: {plot_path}")


def cmd_animate(args):
    """Generate progress.gif with 4-panel view: bars, progression, heatmap, Pareto scatter."""
    import io

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from PIL import Image

    db = load_db(args.db)
    matches = db["matches"]
    if not matches:
        print("No matches to animate.")
        return

    gif_path = Path(args.db).parent / "progress.gif"
    step = args.step
    n = len(matches)

    # Precompute ratings at each match
    print(f"Computing ratings for {n} matches...")
    snapshots = []
    for k in range(1, n + 1):
        partial = {"matches": matches[:k], "versions": db["versions"]}
        r, _ = compute_ratings(partial)
        s = compute_stats(partial)
        snapshots.append((r, s))

    # Build full history
    history = defaultdict(list)
    for k, (ratings, _) in enumerate(snapshots):
        for v, elo in ratings.items():
            history[v].append((k, elo))

    # Assign stable colors per version (collect all that ever appear in top 15)
    top_ever = set()
    for r, _ in snapshots:
        top_ever.update(sorted(r, key=r.get, reverse=True)[:15])
    top_ever = sorted(top_ever)
    cmap = plt.get_cmap("tab20", max(len(top_ever), 1))
    version_colors = {v: cmap(i) for i, v in enumerate(top_ever)}

    # Render frames
    print("Rendering frames...")
    frames = []
    frame_indices = list(range(0, n, step))
    if frame_indices[-1] != n - 1:
        frame_indices.append(n - 1)

    for fi, k in enumerate(frame_indices):
        ratings, stats = snapshots[k]
        sorted_v = sorted(ratings, key=ratings.get, reverse=True)[:15]
        front = pareto_front(sorted_v, _dims(ratings, stats))

        # Per-frame bounds from current top 15
        elos = [ratings[v] for v in sorted_v]
        elo_lo = min(elos) - 50
        elo_hi = max(elos) + 40

        # Collect visible history points for progression bounds
        all_hist_pts = []
        min_match = k
        for v in sorted_v:
            if v in history:
                pts = [(x, y) for x, y in history[v] if x <= k]
                if pts:
                    all_hist_pts.extend(pts)
                    min_match = min(min_match, pts[0][0])
        if all_hist_pts:
            hist_ys = [y for _, y in all_hist_pts]
            prog_elo_lo = min(hist_ys) - 30
            prog_elo_hi = max(hist_ys) + 30
        else:
            prog_elo_lo, prog_elo_hi = elo_lo, elo_hi

        margins = [stats.get(v, {}).get("margin", 0) for v in sorted_v]
        margin_lo = min(margins) - 10
        margin_hi = max(margins) + 10

        fig, axes = plt.subplots(2, 2, figsize=(16, 11))
        fig.suptitle(
            f"Evolution Progress \u2014 Match {k+1}/{n}",
            fontsize=14,
            fontweight="bold",
        )

        # 1. Elo bar chart
        ax = axes[0, 0]
        colors = ["#2ecc71" if v in front else "#3498db" for v in sorted_v]
        ax.barh(range(len(sorted_v)), elos, color=colors)
        ax.set_yticks(range(len(sorted_v)))
        ax.set_yticklabels(sorted_v, fontsize=9)
        ax.set_xlabel("Elo Rating")
        ax.set_title("Top 15 (green = Pareto)")
        ax.invert_yaxis()
        ax.set_xlim(elo_lo, elo_hi)
        for i, v in enumerate(sorted_v):
            ax.text(ratings[v] + 2, i, f"{ratings[v]:.0f}", va="center", fontsize=8)

        # 2. Elo progression (stable colors per version)
        ax = axes[0, 1]
        for v in sorted_v:
            if v in history:
                pts = [(x, y) for x, y in history[v] if x <= k]
                if pts:
                    xs, ys = zip(*pts)
                    style = "-" if v in front else "--"
                    lw = 1.5 if v in front else 0.8
                    ax.plot(xs, ys, style, label=v, linewidth=lw, alpha=0.9,
                            color=version_colors.get(v))
        ax.set_xlabel("Match #")
        ax.set_ylabel("Elo")
        ax.set_title("Rating Progression (Bradley-Terry)")
        ax.set_xlim(max(0, min_match - 2), k + 3)
        ax.set_ylim(prog_elo_lo, prog_elo_hi)
        ax.legend(fontsize=6, loc="upper left", ncol=2)

        # 3. Head-to-head heatmap
        ax = axes[1, 0]
        h2h = defaultdict(lambda: defaultdict(lambda: [0, 0]))
        for m in matches[: k + 1]:
            a, b = m["a"], m["b"]
            h2h[a][b][0] += m["wins_a"]
            h2h[a][b][1] += m["wins_b"]
            h2h[b][a][0] += m["wins_b"]
            h2h[b][a][1] += m["wins_a"]
        nv = len(sorted_v)
        matrix = np.full((nv, nv), np.nan)
        for i, a in enumerate(sorted_v):
            for j, b in enumerate(sorted_v):
                if i != j and h2h[a][b][0] + h2h[a][b][1] > 0:
                    w, l = h2h[a][b]
                    matrix[i, j] = w / (w + l) * 100
        im = ax.imshow(matrix, cmap="RdYlGn", vmin=20, vmax=80, aspect="auto")
        ax.set_xticks(range(nv))
        ax.set_yticks(range(nv))
        ax.set_xticklabels(sorted_v, fontsize=7, rotation=45, ha="right")
        ax.set_yticklabels(sorted_v, fontsize=7)
        ax.set_title("Head-to-Head Win Rate %")
        for i in range(nv):
            for j in range(nv):
                if not np.isnan(matrix[i, j]):
                    color = "white" if matrix[i, j] < 35 or matrix[i, j] > 65 else "black"
                    ax.text(
                        j, i, f"{matrix[i, j]:.0f}",
                        ha="center", va="center", fontsize=7, color=color,
                    )
        fig.colorbar(im, ax=ax, shrink=0.8)

        # 4. Pareto scatter
        ax = axes[1, 1]
        for v in sorted_v:
            s = stats.get(v, {"win_rate": 50, "margin": 0, "games": 0})
            color = "#2ecc71" if v in front else "#95a5a6"
            size = max(20, min(400, s["games"]))
            ax.scatter(
                s["margin"], ratings[v], c=color, s=size,
                edgecolors="black", linewidth=0.5, zorder=3,
            )
            ax.annotate(
                v, (s["margin"], ratings[v]),
                fontsize=7, textcoords="offset points", xytext=(5, 5),
            )
        ax.set_xlabel("Score Margin")
        ax.set_ylabel("Elo Rating")
        ax.set_title("Pareto: Elo vs Margin (size = games played)")
        ax.set_xlim(margin_lo, margin_hi)
        ax.set_ylim(elo_lo, elo_hi)
        if 1500 >= elo_lo and 1500 <= elo_hi:
            ax.axhline(y=1500, color="gray", linestyle=":", alpha=0.5)
        if 0 >= margin_lo and 0 <= margin_hi:
            ax.axvline(x=0, color="gray", linestyle=":", alpha=0.5)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=args.dpi)
        buf.seek(0)
        frames.append(Image.open(buf).copy())
        plt.close(fig)
        buf.close()

        pct = (fi + 1) / len(frame_indices) * 100
        print(f"\r  Frame {fi+1}/{len(frame_indices)} ({pct:.0f}%)", end="", flush=True)
    print()

    # Save GIF — hold last frame longer
    durations = [150] * len(frames)
    durations[-1] = 2000
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
    )
    print(f"Saved: {gif_path} ({len(frames)} frames)")


# ── CLI ─────────────────────────────────────────────────────


def main():
    db_default = os.environ.get("AUTOEVOLVE_DB", "matches.json")

    parser = argparse.ArgumentParser(description="autoevolve tracker")
    parser.add_argument("--db", default=db_default, help="Path to matches.json (env: AUTOEVOLVE_DB)")
    sub = parser.add_subparsers(dest="cmd")

    def _add_db(p):
        """Add --db to a subcommand so it works in both positions."""
        p.add_argument("--db", default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    p = sub.add_parser("record", help="Record a match result")
    _add_db(p)
    p.add_argument("version_a")
    p.add_argument("version_b")
    p.add_argument("--wins", type=int, required=True)
    p.add_argument("--losses", type=int, required=True)
    p.add_argument("--mean-a", type=float, default=None)
    p.add_argument("--mean-b", type=float, default=None)
    p.add_argument("--note", default=None)

    for name in ["leaderboard", "pareto", "matrix", "plot", "progress", "validate"]:
        _add_db(sub.add_parser(name))

    p = sub.add_parser("suggest", help="Suggest next opponent")
    _add_db(p)
    p.add_argument("version")

    p = sub.add_parser("animate", help="Generate progress.gif")
    _add_db(p)
    p.add_argument("--step", type=int, default=1, help="Matches per frame (default: every match)")
    p.add_argument("--dpi", type=int, default=72, help="Resolution (default: 72)")

    commands = {
        "record": cmd_record,
        "leaderboard": cmd_leaderboard,
        "pareto": cmd_pareto,
        "matrix": cmd_matrix,
        "plot": cmd_plot,
        "progress": cmd_progress,
        "validate": cmd_validate,
        "suggest": cmd_suggest,
        "animate": cmd_animate,
    }

    args = parser.parse_args()
    func = commands.get(args.cmd)
    if func:
        func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
