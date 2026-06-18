"""Characterization tests for the rating + Pareto methodology.

These lock in current behavior so later behavior changes (draws, winless
regularization) are intentional and reviewable, not accidental.
"""

import math

from ratings import compute_ratings, compute_stats, pareto_front


def _db(matches):
    versions = {}
    for m in matches:
        versions.setdefault(m["a"], {})
        versions.setdefault(m["b"], {})
    return {"matches": matches, "versions": versions}


# ── compute_ratings ─────────────────────────────────────────


def test_no_matches_returns_empty():
    ratings, counts = compute_ratings(_db([]))
    assert ratings == {}
    assert counts == {}


def test_winner_outrates_loser():
    db = _db([{"a": "v2", "b": "v1", "wins_a": 80, "wins_b": 20}])
    ratings, _ = compute_ratings(db)
    assert ratings["v2"] > ratings["v1"]


def test_even_record_gives_equal_ratings():
    db = _db([{"a": "v2", "b": "v1", "wins_a": 50, "wins_b": 50}])
    ratings, _ = compute_ratings(db)
    assert math.isclose(ratings["v1"], ratings["v2"], abs_tol=1e-6)
    # geometric-mean normalization centers an even pair at the 1500 baseline
    assert math.isclose(ratings["v1"], 1500, abs_tol=1e-6)


def test_order_independent():
    a = _db([
        {"a": "v2", "b": "v1", "wins_a": 70, "wins_b": 30},
        {"a": "v3", "b": "v2", "wins_a": 60, "wins_b": 40},
    ])
    b = _db([
        {"a": "v3", "b": "v2", "wins_a": 60, "wins_b": 40},
        {"a": "v2", "b": "v1", "wins_a": 70, "wins_b": 30},
    ])
    ra, _ = compute_ratings(a)
    rb, _ = compute_ratings(b)
    for v in ra:
        assert math.isclose(ra[v], rb[v], abs_tol=1e-6)


def test_match_counts_tally_all_games():
    db = _db([{"a": "v2", "b": "v1", "wins_a": 80, "wins_b": 20}])
    _, counts = compute_ratings(db)
    assert counts["v1"] == 100
    assert counts["v2"] == 100


def test_400_points_is_ten_to_one():
    # A version that wins ~10:1 against an even-matched field should sit
    # roughly 400 Elo above it.
    db = _db([
        {"a": "v1", "b": "v2", "wins_a": 50, "wins_b": 50},
        {"a": "v3", "b": "v1", "wins_a": 91, "wins_b": 9},
        {"a": "v3", "b": "v2", "wins_a": 91, "wins_b": 9},
    ])
    ratings, _ = compute_ratings(db)
    gap = ratings["v3"] - (ratings["v1"] + ratings["v2"]) / 2
    assert 350 < gap < 450


# ── compute_stats ───────────────────────────────────────────


def test_stats_win_rate_and_opponents():
    db = _db([
        {"a": "v2", "b": "v1", "wins_a": 80, "wins_b": 20},
        {"a": "v2", "b": "v3", "wins_a": 40, "wins_b": 60},
    ])
    stats = compute_stats(db)
    assert stats["v2"]["games"] == 200
    assert stats["v2"]["opponents"] == 2
    assert math.isclose(stats["v2"]["win_rate"], 60.0)


def test_stats_margin_from_means():
    db = _db([{"a": "v2", "b": "v1", "wins_a": 60, "wins_b": 40,
               "mean_a": 3.0, "mean_b": 2.0}])
    stats = compute_stats(db)
    assert math.isclose(stats["v2"]["margin"], 1.0)
    assert math.isclose(stats["v1"]["margin"], -1.0)


# ── pareto_front ────────────────────────────────────────────


def test_pareto_dominated_excluded():
    dims = {
        "x": [10, 1],   # strong on dim 0
        "y": [1, 10],   # strong on dim 1 — mutually non-dominated with x
        "dom": [1, 1],  # dominated by x (and y)
    }
    front = pareto_front(dims)
    assert front == {"x", "y"}


def test_pareto_single_version():
    assert pareto_front({"v1": [1, 2, 3]}) == {"v1"}
