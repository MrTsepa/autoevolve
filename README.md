# autoevolve

Automated iterative improvement through self-play.

A coding agent creates candidate variants of an artifact — a bot, a prompt, a strategy — evaluates them head-to-head, promotes the winners, and repeats. The human sets up the arena and the mutation rules. The agent runs the evolution.

## The GEPA loop

```
┌─────────────────────────────────────────┐
│                                         │
│   Generate   →  create variant(s)       │
│   Evaluate   →  head-to-head matchup    │
│   Promote    →  update Elo ratings      │
│   Archive    →  log everything          │
│                                         │
│   repeat until convergence              │
│                                         │
└─────────────────────────────────────────┘
```

The framework tracks every match result in `matches.json`, computes [Bradley-Terry](https://en.wikipedia.org/wiki/Bradley%E2%80%93Terry_model) ratings (order-independent maximum-likelihood Elo), identifies the Pareto front, and visualizes progress.

## What's here

```
evolve.py      core loop + protocols (Artifact, Evaluator, Mutator)
ratings.py     Bradley-Terry Elo, per-version stats, Pareto front
tracker.py     CLI: leaderboard, record, plot, validate, suggest
example/       real evolution data — 80 versions, 158 matchups
```

## Quick start

```bash
# Record match results
python tracker.py record v2 v1 --wins 62 --losses 38
python tracker.py record v3 v2 --wins 88 --losses 12

# View leaderboard
python tracker.py leaderboard

# Generate progress visualization
python tracker.py plot  # requires matplotlib

# Validate rating reliability
python tracker.py validate

# Get next opponent suggestion (information-theoretic)
python tracker.py suggest v3
```

## Example: real evolution data

The `example/` directory contains real match data from an 80-version strategy evolution. Run the tracker against it:

```bash
python tracker.py --db example/matches.json leaderboard
python tracker.py --db example/matches.json plot
python tracker.py --db example/matches.json validate
```

## How it works

**Rating system.** Bradley-Terry maximum-likelihood estimation, converted to the Elo scale. Unlike sequential Elo (which depends on match order), BT finds the globally optimal ratings that best explain all results simultaneously. 400 points = 10:1 odds.

**Smart matchmaking.** The `suggest` command uses information-theoretic scoring: `score = p*(1-p) / sqrt(games+1)` — prioritizing matchups that are both close (high uncertainty about outcome) and undersampled (few existing games).

**Pareto front.** Versions are compared across multiple dimensions (Elo, score margin, win rate). The Pareto front identifies non-dominated versions — candidates worth branching from for the next mutation.

## Using with a coding agent

The intended workflow:

1. Define your artifact (bot, prompt, strategy) as versioned files
2. Write an evaluator (benchmark script, self-play harness, LLM judge)
3. Give the agent `evolve.py` protocols + your evaluator
4. The agent mutates, evaluates, records, checks leaderboard, repeats

See `evolve.py` for the `Artifact`, `Evaluator`, and `Mutator` protocols, and the `evolve()` loop.

## Prior art

- [autoresearch](https://github.com/karpathy/autoresearch) — autonomous AI research via overnight LLM training experiments
- Bradley-Terry model — [Wikipedia](https://en.wikipedia.org/wiki/Bradley%E2%80%93Terry_model)
