# Prisoner's Dilemma — Worked Example

Evolving strategies for the [Iterated Prisoner's Dilemma](https://en.wikipedia.org/wiki/Prisoner%27s_dilemma#The_iterated_prisoner's_dilemma) using autoevolve. This example demonstrates the full workflow: seed a naive strategy, let an LLM agent mutate and benchmark, track progress with Elo ratings, and discover emergent game-theoretic dynamics.

![Evolution Progress](progress.png)

## The game

Each round, two players simultaneously **cooperate** or **defect**:

|          | Cooperate | Defect |
|----------|-----------|--------|
| **Cooperate** | 3, 3  | 0, 5   |
| **Defect**    | 5, 0  | 1, 1   |

Mutual cooperation beats mutual defection (3 > 1), but defecting against a cooperator is tempting (5 > 3). Each game lasts 200 rounds. A 5% noise rate randomly flips moves, forcing strategies to be robust to accidental defections.

## How to run

```bash
# Run a match (100 games × 200 rounds)
uv run examples/prisoners_dilemma/arena.py v11 v2 --games 100

# Check the leaderboard
uv run tracker.py --db examples/prisoners_dilemma/matches.json leaderboard

# Get a suggested opponent
uv run tracker.py --db examples/prisoners_dilemma/matches.json suggest v11

# Visualize progress
uv run tracker.py --db examples/prisoners_dilemma/matches.json progress
```

## Strategy interface

Each strategy is a Python file in `strategies/vN.py`:

```python
def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    """Return True to cooperate, False to defect."""
```

## The evolution

Starting from a deliberately naive seed, the agent evolved 20 strategies across ~60 head-to-head matchups. Five versions mark the key breakthroughs:

### v1 — Always Cooperate (seed)

```python
def strategy(my_history, opp_history):
    return True
```

The simplest possible strategy. Cooperates unconditionally, scoring 3.0/round in mutual cooperation — but gets exploited by anything that defects. Elo: **946** (last place).

### v2 — Tit-for-Tat

```python
def strategy(my_history, opp_history):
    if not opp_history:
        return True
    return opp_history[-1]
```

The classic: cooperate first, then mirror the opponent's last move. Retaliatory enough to punish defectors, cooperative enough to sustain mutual cooperation. Dominates the early field. Elo: **1964** (#2).

### v4 — Pavlov (Win-Stay, Lose-Shift)

```python
def strategy(my_history, opp_history):
    if not my_history:
        return True
    good = opp_history[-1]  # CC=3 or DC=5 are "good"
    if good:
        return my_history[-1]  # stay
    return not my_history[-1]  # shift
```

The first big insight: Pavlov can escape mutual-defection spirals that TFT cannot. When both defect (DD=1), Pavlov switches to cooperation, breaking the deadlock. TFT just keeps mirroring defection forever. This gives Pavlov a structural edge over TFT (57% win rate head-to-head). Elo: **1557** (#8 — held back by later strategies).

### v9 — Soft Pavlov

```python
def strategy(my_history, opp_history):
    if not my_history:
        return True
    good = opp_history[-1]
    if good:
        return my_history[-1]
    if random.random() < 0.15:
        return my_history[-1]  # forgive 15%
    return not my_history[-1]
```

The first strategy to beat Pavlov (58-37). Adds 15% stochastic forgiveness on bad outcomes — just enough to dampen noise-driven oscillation without becoming exploitable. Still loses to TFT, but proves Pavlov is beatable. Elo: **1479** (#9).

### v11 — Gradual (champion)

```python
def strategy(my_history, opp_history):
    if not opp_history:
        return True
    # Replay to reconstruct state: defection_count, punish, peace
    for i in range(len(opp_history)):
        if punish_remaining > 0: ...
        elif peace_remaining > 0: ...
        else:  # FREE — detect defections
            if not opp_history[i]:
                defection_count += 1
                punish_remaining = defection_count
    return punish_remaining <= 0
```

Based on [Beaufils et al. (1996)](https://www.jstor.org/stable/40602778). Proportional punishment: the Nth defection triggers N rounds of retaliation, followed by 2 cooperation rounds as a peace signal. Early defections (likely noise) get light punishment; persistent defectors face escalating consequences. Crushes Pavlov 99-0 and dominates the field. Elo: **1965** (#1).

## The rock-paper-scissors at the top

The most interesting finding: the top three strategies form a non-transitive cycle.

```
Gradual (v11) → beats → Pavlov (v4) → beats → TFT (v2) → beats → Gradual (v11)
     99-0                    57-43                  85-14
```

- **Gradual beats Pavlov** because escalating punishment stops Pavlov's exploitation attempts cold.
- **Pavlov beats TFT** because Pavlov can escape DD spirals (switches to C after DD) while TFT mirrors forever.
- **TFT beats Gradual** because Gradual's punishment creates a feedback loop — noise during punishment phases generates more "defections" that Gradual detects, triggering escalation.

No single strategy dominates all three. This mirrors a well-known result in evolutionary game theory: in noisy environments, the strategy space has no global optimum — only a shifting Pareto front.

## Final leaderboard

```
    Version         Elo    WR%   Margin  Games  Pareto
————————————————————————————————————————————————————
  1 v11            1965  85.8%    +0.4   1080 *
  2 v2             1964  88.9%    +0.1   1519 *
  3 v19            1803  64.8%    +0.2    492
  4 v13            1761  55.8%    +0.1    378
  5 v16            1701  56.5%    +0.1    483
  6 v20            1643  47.1%    +0.0    393
  7 v8             1562  53.9%    +0.6    284 *
  8 v4             1557  56.0%    +0.1   1551
  9 v9             1479  33.6%    +0.2    672
 10 v14            1476  38.1%    -0.1    488
 11 v6             1398  42.4%    -0.0    283
 12 v12            1375  31.6%    -0.0    393
 13 v3             1321  38.1%    -0.0    294
 14 v15            1281  27.6%    -0.1    392
 15 v7             1233  31.8%    -0.1    292
 16 v5             1036  21.1%    -0.2    289
 17 v1              946   6.7%    -0.7   1563
```

20 versions evolved. 5 reached the Pareto front. 15 were discarded — a realistic mutation/selection ratio.

## What this demonstrates

1. **The autoevolve workflow works.** From a trivial seed (Always Cooperate, Elo 946) to a literature-quality champion (Gradual, Elo 1965) through targeted mutation and selection.

2. **Diagnosis-driven mutation beats random search.** The agent read losing matchups, identified *why* strategies failed (noise spirals, exploitation, escalation feedback), and proposed targeted fixes. This is the key advantage over blind evolutionary search.

3. **Most mutations fail — and that's fine.** 15 of 20 versions were discarded. The tracker's Elo ratings and Pareto front make it cheap to identify winners and prune losers.

4. **Non-trivial dynamics emerge.** The rock-paper-scissors cycle at the top wasn't designed — it was discovered through the evolution process, matching decades of game theory research.

## Files

| File | Purpose |
|------|---------|
| `arena.py` | Head-to-head evaluation harness |
| `program.md` | Agent instructions for the evolution loop |
| `matches.json` | Full match history (append-only) |
| `progress.png` | Evolution progress visualization |
| `strategies/v1.py` | Seed strategy (Always Cooperate) |
| `strategies/v2.py–v20.py` | Evolved strategies |

## Extending this example

To continue evolving from here:

1. Read `program.md` for the full agent workflow
2. Check the leaderboard and pick a parent from the Pareto front
3. Analyze its weaknesses against top opponents
4. Write a new `strategies/v21.py` targeting those weaknesses
5. Benchmark against 2–3 opponents and record results

The TFT–Gradual matchup remains unsolved — can you evolve a strategy that beats both?
