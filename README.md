# autoevolve

Let a coding agent evolve your strategy overnight.

You define the arena and the rules. The agent runs the evolution — mutating strategies, benchmarking them head-to-head, and promoting the winners. This repo provides the loop and the tracking infrastructure.

Inspired by [GEPA](https://github.com/gepa-ai/gepa) (Genetic-Pareto evolutionary optimization) and [autoresearch](https://github.com/karpathy/autoresearch) (autonomous AI research overnight). Where GEPA optimizes prompts and text parameters via LLM reflection, autoevolve focuses on self-play: evolving strategies, bots, or any artifact where quality is measured by head-to-head competition.

## The idea

Give an AI coding agent a strategy template and an evaluation harness. The agent runs the loop:

```
Generate   →  create a new version of the strategy
Evaluate   →  benchmark against previous versions
Promote    →  update ratings, crown the new best
Archive    →  log everything for traceability

repeat until convergence (or until you wake up)
```

Every match result is recorded in `matches.json`. Ratings are computed from scratch each time using [Bradley-Terry](https://en.wikipedia.org/wiki/Bradley%E2%80%93Terry_model) maximum likelihood — order-independent and globally optimal. The Pareto front identifies which versions are worth branching from next.

## Example: 80 versions evolved through self-play

![Evolution Progress](example/progress.gif)

Real data from a strategy evolution experiment. 80 versions, 235 matchups, tracked and rated automatically.

## What's here

```
program.md     agent instructions — the main file you edit
evolve.py      core loop + protocols (Artifact, Evaluator, Mutator)
ratings.py     Bradley-Terry Elo, per-version stats, Pareto front
tracker.py     CLI: leaderboard, record, plot, validate, suggest, animate
example/       real evolution data with animated visualization
```

The agent only touches the strategy files. Everything else is infrastructure.

## Quick start

1. Clone the repo
2. Edit `program.md`: define your environment, strategy format, and evaluation command
3. Point your coding agent at the repo
4. Let it evolve

```bash
# The agent runs these as part of the loop:
python tracker.py leaderboard                              # check standings
python tracker.py record v2 v1 --wins 62 --losses 38      # log result
python tracker.py suggest v2                               # pick next opponent
python tracker.py plot                                     # visualize progress
```

## Tracker commands

| Command | What it does |
|---------|-------------|
| `record` | Log a match result |
| `leaderboard` | Show Elo rankings with Pareto front |
| `pareto` | Show non-dominated versions |
| `matrix` | Head-to-head win rate table |
| `plot` | Generate progress.png (4-panel) |
| `validate` | Prediction accuracy + bootstrap CIs |
| `suggest` | Next opponent (information-theoretic) |
| `animate` | Generate progress.gif from match history |

All commands accept `--db path/to/matches.json`.

## How the ratings work

**Bradley-Terry MLE** finds the globally optimal ratings that best explain all match results simultaneously. Unlike sequential Elo, it doesn't depend on match order. 400 points = 10:1 win odds.

**Information-theoretic matchmaking**: `score = p*(1-p) / sqrt(games+1)` — prioritizes matchups that are both close (uncertain outcome) and undersampled.

**Pareto front**: versions compared across Elo, score margin, and win rate. Non-dominated versions are the best candidates to branch from.

## Prior art

- [GEPA](https://github.com/gepa-ai/gepa) — Genetic-Pareto evolutionary optimization of text parameters via LLM reflection
- [autoresearch](https://github.com/karpathy/autoresearch) — autonomous AI research via overnight LLM training experiments
- [Bradley-Terry model](https://en.wikipedia.org/wiki/Bradley%E2%80%93Terry_model) — pairwise comparison probability model
