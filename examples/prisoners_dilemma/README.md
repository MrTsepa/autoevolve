# Prisoner's Dilemma — Worked Example

Evolving strategies for the [Iterated Prisoner's Dilemma](https://en.wikipedia.org/wiki/Prisoner%27s_dilemma#The_iterated_prisoner's_dilemma) using autoevolve. Starting from a trivial seed (Always Cooperate), the agent evolved 9 strategies and discovered a champion that combines proportional punishment with opponent classification — nearly tying the classic Tit-for-Tat while dominating everything else.

![Evolution Progress](progress.png)

## The game

Each round, two players simultaneously **cooperate** or **defect**:

|          | Cooperate | Defect |
|----------|-----------|--------|
| **Cooperate** | 3, 3  | 0, 5   |
| **Defect**    | 5, 0  | 1, 1   |

200 rounds per game, 100 games per match, 5% noise rate.

## How to run

```bash
# Run a match and auto-record
uv run examples/prisoners_dilemma/arena.py v9 v2 --games 100 --record

# Diagnose with move-by-move trace
uv run examples/prisoners_dilemma/arena.py v9 v2 --trace --seed 42

# Check standings
uv run tracker.py leaderboard --db examples/prisoners_dilemma/matches.json

# Get suggested next opponent
uv run tracker.py suggest v9 --db examples/prisoners_dilemma/matches.json
```

## Evolution journey

### v1 — Always Cooperate (seed)

Cooperates unconditionally. Gets exploited by everything. Elo: **-177**.

### v2 — Tit-for-Tat

Mirror opponent's last move. The classic baseline. Elo: **2099** (#3).

### v3 — Pavlov

Win-stay, lose-shift. Edges TFT (60-40) via DD-escape but gets crushed by Gradual. Elo: **1591** (#6).

### v4 — Gradual

Proportional punishment (Beaufils 1996). Crushes Pavlov 100-0 but loses to TFT 9-91. Using `--trace` revealed the exact mechanism: each noise event adds to the defection counter permanently, causing late-game punishments of 5+ rounds. TFT mirrors these, creating extended mutual defection. Elo: **1884** (#4).

### v5 — Gradual with decaying counter (failed)

Attempted fix: decay the counter after each cycle. Made punishment too weak — loses to everything. Elo: **621** (#7).

### v6 — Probe + Classify (failed)

Probed on rounds 5-6 to detect TFT. Classification worked but noise corrupted the probe ~19% of the time. Misclassified games used Gradual vs TFT and lost badly. Elo: **1672** (#5).

### v7 — Gradual with auto-classification (not kept)

Used Gradual's own punishment phases as natural probes. Classified correctly but switched to always-cooperate, which still loses to TFT (free DC=5 on every noise event).

### v8 — Gradual with TFT fallback

Key fix from v7: after detecting a mirror, switch to **TFT mode** (not always-cooperate). This cancels noise symmetrically. Reduced TFT loss from 9-87 to 25-52. Elo: **2114** (#2).

### v9 — Faster classification (champion)

Lowered detection threshold from 5 to 3 observations, mirroring threshold from 70% to 60%. Classifies TFT after ~2 punishment cycles instead of ~4, reducing early-game damage. Nearly ties TFT at **40-47**. Elo: **2196** (#1).

## Key insight: diagnosis via `--trace`

Gradual (v4) crushes Pavlov but loses to TFT. Why? The `--trace` tool showed the problem in 30 seconds:

```
 Rnd      v4      v2    Pay       Total  Note
  10       C       D  0,5     19-34    v2 noise    ← noise triggers punishment
  11       D       C  5,0     24-34                 ← punishment round 1
  12       D       D  1,1     25-35                 ← TFT mirrors punishment
  13       D       D  1,1     26-36                 ← escalating...
  14       C       D  0,5     26-41                 ← peace phase, TFT still defecting
```

Seeing "round 14: peace phase but TFT still defecting" made the solution obvious: detect the mirror, stop punishing it. Three iterations later, v9 nearly ties TFT while dominating everything else.

## Final leaderboard

```
    Version         Elo    WR%   Margin  Games   Opp
——————————————————————————————————————————————————————————
  1 v9             2196  87.3%    +0.4    659    7 *
  2 v8             2114  81.7%    +0.4    651    7
  3 v2             2099  80.0%    +0.1    646    7
  4 v4             1884  60.6%    +0.3    680    7
  5 v6             1672  34.6%    -0.0    584    6
  6 v3             1591  38.7%    +0.2    688    7
  7 v5              621  16.5%    -0.5    600    6
  8 v1             -177   0.1%    -0.8    700    7
```

## Head-to-head matrix

```
              v1      v2      v3      v4      v5      v6      v8      v9
      v1       —      0%      0%      0%      1%      0%      0%      0%
      v2    100%       —     40%     91%    100%     98%     68%     54%
      v3    100%     60%       —      0%    100%     12%      1%      0%
      v4    100%      9%    100%       —    100%     96%      9%      5%
      v5     99%      0%      0%      0%       —              0%      0%
      v6    100%      2%     88%      4%               —      5%      3%
      v8    100%     32%     99%     91%    100%     95%       —     35%
      v9    100%     46%    100%     95%    100%     97%     65%       —
```

Dense coverage thanks to `suggest` — every version tested against 6-7 opponents.
