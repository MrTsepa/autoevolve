# Program

You are an agent evolving a strategy through automated self-play.

## Infrastructure (do not modify)

- `evolve.py` — core protocols and evolution loop
- `ratings.py` — Bradley-Terry Elo ratings
- `tracker.py` — CLI for tracking and analysis

## Your job

Each iteration:

1. **Check standings**: `uv run tracker.py leaderboard`
2. **Pick a parent**: choose a version from the Pareto front to branch from
3. **Analyze**: look at win/loss patterns, replay traces, failure modes
4. **Mutate**: create a new version with targeted improvements
5. **Evaluate**: benchmark the new version against top opponents
6. **Record**: `uv run tracker.py record vNew vOld --wins W --losses L`
7. **Reflect**: did it improve? what to try next?
8. **Repeat**

## Guidelines

- One version per iteration. Name sequentially: v1, v2, v3, ...
- Minimum 100 games per matchup for statistical significance
- Match data is append-only — never delete results
- Use `uv run tracker.py suggest vN` to pick the most informative opponent
- Branch from Pareto-front versions, not just the highest-rated
- When stuck, analyze replays or traces to diagnose specific failure modes
- Commit matches.json after each significant benchmark round

## Defining your experiment

To use this framework, fill in the sections below.

### Environment

_What arena do the strategies compete in?_

(e.g., game simulator, prompt evaluation harness, model training benchmark)

### Strategy format

_What does a "version" look like?_

(e.g., a Python file, a C++ binary, a prompt template, a config file)

### Evaluation command

_How do you run a head-to-head benchmark?_

(e.g., `uv run benchmark.py --player-a vN --player-b vM -n 100`)
