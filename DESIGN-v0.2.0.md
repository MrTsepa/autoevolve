# autoevolve v0.2.0 — Design

**Theme:** *The self-play methodology + a generic skill that runs it.*

The durable asset in this repo is the **concept and the contract** — improve
anything you can score head-to-head, select opponents intelligently, branch
from the Pareto front, and stop when progress plateaus. The Python
`evolve()` orchestration loop has never been worth anything because nothing
runs it. v0.2.0 resolves this by making **the skill the runner**: Claude is
the Mutator and the loop driver, and the CLI provides the methodology
primitives (evaluation, ratings, opponent selection, stopping signal).

## Guiding decisions

1. **One loop, in the skill.** Remove the Python `evolve()` loop and the
   `Mutator` protocol. Claude mutates and decides; the CLI evaluates, rates,
   suggests opponents, and reports when to stop.
2. **The `Evaluator` is a command contract, not a Python class to subclass.**
   Any arena conforms by exposing an evaluation command with standardized
   output. This keeps "generic" honest — it works for non-agent users too,
   and it is testable.
3. **Backward compatible data.** Every existing `matches.json` stays
   readable. All new fields are optional.

## The Evaluator contract

An arena conforms to autoevolve by providing a command that pits two versions
against each other and prints a single JSON object on stdout:

```
<eval-cmd> --a vN --b vM -n 100
→ {"wins_a": int, "wins_b": int, "draws": int, "mean_a": float?, "mean_b": float?}
```

- `wins_a` / `wins_b` / `draws` are required; `mean_a` / `mean_b` optional
  (used for the score-margin Pareto dimension).
- The command is configured per experiment via `AUTOEVOLVE_EVAL_CMD` (and
  recorded in `program.md`).
- `evolve.py` keeps the `Evaluator` Protocol as the typed expression of this
  contract; `arena.py`'s `run_match` already returns exactly this shape.

## Three pillars

### Pillar 1 — Formalize the contract (the concept)

- Document the Evaluator command contract (above).
- `evolve.py`: keep `MatchResult`, `load_db`, `save_db`, `record`, and the
  `Evaluator` Protocol. **Remove** `evolve()`, `Artifact`(reduce), and
  `Mutator`.
- Update README architecture section and SKILL.md to stop advertising a
  Python loop that does not run.

### Pillar 2 — Make the methodology runnable & generic (the bridge)

New / changed `tracker.py` commands:

- **`eval vN vM -n 100`** — run the configured arena command, parse the
  contract JSON, and record the match (draws included). This is what turns
  the tracker from a passive ledger into a runnable engine.
- **`gauntlet vN --n 3 [--against pareto|top|all]`** — emit the N most
  informative opponents for `vN` in one shot (batch `suggest`). Encodes the
  already-instructed "≥3 opponents" rule as one command.
- **global `suggest`** (no version arg) — return the single most informative
  *pair* across the whole pool, for "what should I run next?".
- **`status`** — best version + 95% CI, whether the running-best has stalled
  over the last N versions, coverage gaps (the `?` <3-opponent flag), and
  disconnected-component warnings. The stop signal for the loop.
- **`init <name>`** — scaffold an experiment dir (`program.md` + empty
  `matches.json`) so the skill can bootstrap from a one-line description.

### Pillar 3 — The generic skill *is* the loop (the runner)

Rewrite `SKILL.md` / `program.md` into an explicit autonomous procedure:

```
bootstrap → loop( mutate → eval vs gauntlet → rate → branch from Pareto → status )
          → stop on plateau or budget
```

- Claude's job: **mutate** (write the next version) and **decide** (which
  parent, when to stop).
- The CLI's job: **eval, rate, select opponents, signal stop.**
- Wire the Prisoner's Dilemma example to run end-to-end through the contract
  (`arena.py` is already 90% there) as the proof it is generic.

## Methodology improvements (enablers of the loop)

- **Draws.** `MatchResult.draws: int = 0`; `record --draws`; `eval` captures
  them. Bradley-Terry handles ties via the ½-credit rule (each draw counts as
  half a win to both sides). `compute_stats` reports draws; win rate becomes
  score `(W + ½D)/games`. Missing `draws` ⇒ 0, so old data is unaffected.
- **Lineage.** `db["versions"][v]` gains optional `{parent, created, note}`.
  New `meta vN --parent vK --note "…"` sets it (append-only friendly). New
  `tree` command (ASCII genealogy) and a genealogy plot (layered: depth =
  generation, color = kept/Pareto, edges parent→child) — the new hero visual.
  Today the `progress` plot *infers* "kept" from running-best Elo because real
  lineage did not exist.
- **Confidence intervals + stopping.** Lift bootstrap CI out of `validate`
  into `ratings.bootstrap_ci(db)`; reuse in `leaderboard --ci` and `status`.

## Behavior-preserving refactors

| # | Change | Where | Win |
|---|--------|-------|-----|
| R1 | Remove dead `evolve()`/`Mutator`; slim to data layer + `Evaluator` contract | `evolve.py` | removes the two-loop contradiction |
| R2 | Extract shared panel helpers used by `plot` & `animate` | `tracker.py` | ~120 LOC of duplication gone; views can't drift |
| R3 | One warm-started `rating_history(db)`; `compute_ratings(warm_start=…)` | `ratings.py`, `tracker.py` | long-run animate goes from N cold MLE solves to near-linear |
| R4 | Drop unused `versions` arg from `pareto_front(dimensions)` | `ratings.py` | callers pass a list it ignores |
| R5 | `cmd_record` builds a `MatchResult` and calls `record()` | `tracker.py` | single write path (draws handled once) |
| R6 | `plot`→`dashboard.png`, `progress`→`progress.png`; add `--out` | `tracker.py` | two commands silently overwrite one file today |
| R7 | Regularize winless/lossless versions in MLE | `ratings.py` | 0-win version no longer freezes at 1500 |
| R8 | Detect & warn on disconnected match graph | `ratings.py`/`status` | cross-component ratings aren't comparable |

## Reliability

- `tests/` (pytest): `compute_ratings` (incl. draws, winless, disconnected),
  `pareto_front`, suggest/gauntlet scoring, lineage-tree building, DB
  round-trip, draw arithmetic. Pure functions — fast, no matplotlib.
- GitHub Actions: `uv sync` + ruff + pytest → green badge for the release.

## Sequencing (small, reviewable PRs)

1. **Refactor + tests + CI** (R1–R8, no behavior change) — safe foundation.
2. **Draws** (schema-compatible).
3. **`eval` contract + `init`** (the runnable bridge).
4. **Lineage + `tree` + genealogy plot.**
5. **CIs + `status` + global `suggest` + `gauntlet`.**
6. **Skill/`program.md` rewrite + PD example wired end-to-end.**
7. **Docs + CHANGELOG + README pin bump → tag `v0.2.0`.**

**Compatibility note:** the only visible change for existing users is the
`plot`/`progress` output filename split (R6); called out in the CHANGELOG.
