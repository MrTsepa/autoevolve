"""Bradley-Terry maximum-likelihood ratings, per-version stats, and Pareto front."""

import math
from collections import defaultdict


def compute_ratings(db: dict, initial: float = 1500) -> tuple[dict, dict]:
    """Compute Elo-scale ratings via Bradley-Terry maximum likelihood.

    Order-independent: finds globally optimal ratings that best explain all
    match results simultaneously. 400 points = 10:1 win odds.

    Returns (ratings, match_counts).
    """
    h2h = defaultdict(lambda: defaultdict(int))
    match_counts = defaultdict(int)
    versions = set()

    for m in db["matches"]:
        a, b = m["a"], m["b"]
        wa, wb = m["wins_a"], m["wins_b"]
        h2h[a][b] += wa
        h2h[b][a] += wb
        total = wa + wb
        match_counts[a] += total
        match_counts[b] += total
        versions.add(a)
        versions.add(b)

    if not versions:
        return {}, {}

    versions = sorted(versions)
    r = {v: 1.0 for v in versions}

    total_wins = {}
    pair_games = defaultdict(lambda: defaultdict(int))
    for v in versions:
        total_wins[v] = sum(h2h[v][u] for u in versions if u != v)
    for m in db["matches"]:
        a, b = m["a"], m["b"]
        n = m["wins_a"] + m["wins_b"]
        pair_games[a][b] += n
        pair_games[b][a] += n

    # Iterative MLE
    for _ in range(200):
        max_change = 0
        for v in versions:
            if total_wins[v] == 0:
                continue
            denom = sum(
                pair_games[v][u] / (r[v] + r[u])
                for u in versions
                if u != v and pair_games[v][u] > 0
            )
            if denom < 1e-12:
                continue
            new_r = total_wins[v] / denom
            max_change = max(max_change, abs(new_r - r[v]) / max(r[v], 1e-12))
            r[v] = new_r
        if max_change < 1e-8:
            break

    # Normalize by geometric mean
    geo_mean = math.exp(sum(math.log(r[v]) for v in versions) / len(versions))
    for v in versions:
        r[v] /= geo_mean

    ratings = {v: 400 * math.log10(max(r[v], 1e-12)) + initial for v in versions}
    return ratings, dict(match_counts)


def compute_stats(db: dict) -> dict:
    """Per-version aggregates: win rate, score margin, total games."""
    stats = defaultdict(lambda: {"wins": 0, "losses": 0, "scores": [], "opp_scores": []})

    for m in db["matches"]:
        a, b = m["a"], m["b"]
        stats[a]["wins"] += m["wins_a"]
        stats[a]["losses"] += m["wins_b"]
        stats[b]["wins"] += m["wins_b"]
        stats[b]["losses"] += m["wins_a"]

        if "mean_a" in m and "mean_b" in m:
            n = m["wins_a"] + m["wins_b"]
            stats[a]["scores"].extend([m["mean_a"]] * n)
            stats[a]["opp_scores"].extend([m["mean_b"]] * n)
            stats[b]["scores"].extend([m["mean_b"]] * n)
            stats[b]["opp_scores"].extend([m["mean_a"]] * n)

    result = {}
    for v, s in stats.items():
        total = s["wins"] + s["losses"]
        wr = s["wins"] / total * 100 if total else 0
        margin = 0
        if s["scores"] and s["opp_scores"]:
            margin = (
                sum(s["scores"]) / len(s["scores"])
                - sum(s["opp_scores"]) / len(s["opp_scores"])
            )
        result[v] = {"win_rate": wr, "games": total, "margin": margin}
    return result


def pareto_front(versions: list, dimensions: dict) -> set:
    """Find Pareto-optimal versions across multiple dimensions.

    dimensions: {version: [dim1_val, dim2_val, ...]}
    Returns set of non-dominated version names.
    """
    front = set()
    vlist = list(dimensions.keys())

    for i, v in enumerate(vlist):
        dominated = False
        for j, u in enumerate(vlist):
            if i == j:
                continue
            vals_v, vals_u = dimensions[v], dimensions[u]
            if all(vals_u[d] >= vals_v[d] for d in range(len(vals_v))) and any(
                vals_u[d] > vals_v[d] for d in range(len(vals_v))
            ):
                dominated = True
                break
        if not dominated:
            front.add(v)
    return front
