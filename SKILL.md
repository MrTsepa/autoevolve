---
name: autoevolve
description: Iteratively improve code, strategies, or prompts through mutation, evaluation, and selection
---

# AutoEvolve

Iteratively improve code, strategies, or prompts through mutation, evaluation, and selection.

## What this skill does

AutoEvolve teaches you to run an evolutionary improvement loop on any artifact that can be evaluated through head-to-head comparison. You mutate a candidate, benchmark it against previous versions, rate all versions using Bradley-Terry maximum likelihood estimation, and branch from the strongest candidates on the Pareto front.

The loop: **Mutate -> Evaluate -> Rate -> Branch -> Repeat**

You act as the mutation engine -- reading code, analyzing why a version lost, and proposing targeted fixes. The infrastructure handles statistical ratings, opponent selection, and progress tracking.

## When to use this skill

Use AutoEvolve when the user wants to:

- **Evolve game bots** -- improve strategies through self-play in board games, card games, or simulations
- **Optimize prompts** -- two prompt variants produce outputs, an LLM judge picks the winner
- **Tune heuristic policies** -- evolve readable decision rules instead of opaque weights
- **Improve trading/search strategies** -- backtest candidates on the same historical data
- **Co-evolve adversarial agents** -- red team vs blue team, both sides get stronger

The common requirement: **two versions can compete, and you can decide which one won.**

Do NOT use this skill for:
- Tasks with no measurable comparison (use standard coding instead)
- One-shot generation (no iteration needed)
- Tasks where a unit test or loss function is sufficient (standard testing is simpler)

## Inputs and expected project context

### Required

- **`program.md`** -- Defines the experiment: what arena the strategies compete in, what a "version" looks like (Python file, config, prompt template), and how to run a head-to-head benchmark.
- **An evaluation command** -- A way to run two versions against each other and get win/loss counts.
- **A seed candidate** -- The initial version (`v1`) to start evolving from. Can be trivial.

### Provided by the framework

- **`evolve.py`** -- Core protocols: `Artifact`, `Evaluator`, `Mutator`, plus the evolution loop and match database I/O.
- **`ratings.py`** -- Bradley-Terry MLE ratings (order-independent), per-version stats, Pareto front computation.
- **`tracker.py`** -- CLI for recording matches, viewing leaderboards, generating plots, and getting opponent suggestions.
- **`matches.json`** -- Append-only match database. Created automatically on first record.

### Dependencies

- Python >= 3.11, no required dependencies (pure Python core)
- Optional: `matplotlib`, `numpy` for plotting; `pillow` for animation
- Package manager: `uv` (recommended)

## Step-by-step workflow

### Phase 1: Setup

1. Ensure the autoevolve infrastructure is available.
2. Fill in `program.md` with: the environment (arena), strategy format (file type, interface), and evaluation command.
3. Create a seed strategy as `v1`. It can be naive.
4. Verify the evaluation command works by running `v1` against itself.

### Phase 2: Evolution loop

For each iteration:

1. **Check standings**: `uv run tracker.py leaderboard`
2. **Pick a parent** from the Pareto front (marked `*` on the leaderboard).
3. **Pick an opponent**: `uv run tracker.py suggest vN` -- finds the most informative matchup via information-theoretic scoring. Do not cherry-pick opponents.
4. **Analyze**: Read the parent's code. Review win/loss patterns. Replay traces if available.
5. **Mutate**: Create `vN+1` with targeted improvements. One version per iteration. Name sequentially.
6. **Evaluate**: Benchmark against at least 3 opponents, minimum 100 games each:
   ```bash
   uv run tracker.py record vNew vOld --wins W --losses L
   ```
7. **Reflect**: Check updated ratings. What improved? What failure modes remain?
8. **Commit** `matches.json` after each benchmark round.
9. **Repeat** until progress plateaus or budget runs out.

### Phase 3: Analysis

```bash
uv run tracker.py leaderboard    # Elo ratings with Pareto front flags
uv run tracker.py matrix          # Head-to-head win rate table
uv run tracker.py progress        # Elo-over-time staircase chart
uv run tracker.py plot            # 4-panel overview
uv run tracker.py validate        # Prediction accuracy + bootstrap CIs
uv run tracker.py suggest vN      # Next opponent (information-theoretic)
uv run tracker.py animate         # progress.gif over time
```

## Examples

### Example 1: Evolving game strategies

```
User: Help me evolve a Prisoner's Dilemma strategy.

Steps taken:
1. Read program.md for IPD rules and strategy interface
2. Created v1 (Always Cooperate) as naive seed
3. Mutated to v2 (Tit-for-Tat) -- classic baseline
4. Benchmarked v2 vs v1: 62-38 wins
5. Recorded: uv run tracker.py record v2 v1 --wins 62 --losses 38
6. Continued evolving through v3 (Pavlov), v4 (Gradual), ...
7. Used --trace to diagnose failure modes (noise-induced punishment spirals)
8. v9 achieved 87% overall win rate by combining Gradual with TFT detection
```

### Example 2: Prompt optimization

```
User: I have two prompt templates for summarization. Help me evolve better ones.

Steps taken:
1. Defined program.md: arena = LLM judge comparing summaries, strategy = prompt template
2. Created v1 (baseline prompt)
3. Mutated to v2 with improved instruction structure
4. Evaluated: had LLM judge score 100 summary pairs, v2 won 58-42
5. Recorded result, checked leaderboard
6. Continued iterating on phrasing, few-shot examples, constraints
```

### Example 3: Evolving a heuristic search

```
User: Optimize my beam search heuristic for a planning problem.

Steps taken:
1. Defined program.md: arena = planning benchmark, strategy = heuristic function
2. Seeded with simple Manhattan distance heuristic
3. Each mutation adjusted weights, added pattern databases, or changed tie-breaking
4. Evaluation: ran both heuristics on 200 problem instances, compared solve rates
5. After 12 iterations, heuristic solved 94% of instances (up from 71%)
```

## Key guidelines

- **One version per iteration**. Name sequentially: v1, v2, v3, ...
- **Minimum 100 games per matchup** for statistical significance.
- **Match data is append-only** -- never delete results from `matches.json`.
- **Always use `suggest`** to pick opponents. Manual cherry-picking leads to sparse coverage and unreliable ratings.
- **Benchmark against at least 3 opponents** before drawing conclusions. Versions with fewer opponents are flagged with `?` on the leaderboard.
- **Branch from the Pareto front**, not just the highest-rated version.
- **When stuck, analyze traces** to diagnose specific failure modes rather than making random changes.

## How the ratings work

- **Bradley-Terry MLE** finds globally optimal ratings from all match results simultaneously. Unlike sequential Elo, it does not depend on match order. 400 points = 10:1 win odds.
- **Information-theoretic matchmaking**: `score = p*(1-p) / sqrt(games+1)` prioritizes matchups that are close (uncertain outcome) and undersampled.
- **Pareto front**: versions compared across Elo, score margin, and win rate. Non-dominated versions are the best candidates to branch from.

## Limitations and safety notes

- **Cost**: Each mutation + evaluation cycle costs LLM API calls and compute time. Budget accordingly.
- **Local optima**: Evolutionary search can get stuck. If progress plateaus, try a radically different approach rather than incremental tweaks.
- **Statistical noise**: Small sample sizes produce unreliable ratings. Stick to the 100-game minimum.
- **Not a substitute for design**: AutoEvolve finds improvements within a design space. If the design space is wrong (e.g., wrong game model, wrong evaluation metric), evolution will optimize the wrong thing.
- **Adversarial domains**: When co-evolving attack/defense, ensure evaluation stays within ethical and legal bounds. Do not evolve real exploits against production systems.
- **Reproducibility**: Set random seeds where possible. Record environment details in `program.md` notes.
- **LLM reliability**: Mutations are only as good as the agent's code understanding. Review generated code before deploying evolved artifacts to production.
