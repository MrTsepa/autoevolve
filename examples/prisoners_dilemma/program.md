# Prisoner's Dilemma — Evolution Program

You are evolving strategies for the **Iterated Prisoner's Dilemma** (IPD) using autoevolve.

## Rules

Each round, two players simultaneously choose to **cooperate** (C) or **defect** (D).

| Player A | Player B | A's payoff | B's payoff |
|----------|----------|------------|------------|
| C        | C        | 3          | 3          |
| C        | D        | 0          | 5          |
| D        | C        | 5          | 0          |
| D        | D        | 1          | 1          |

- Mutual cooperation (3,3) beats mutual defection (1,1), but defecting against a cooperator is tempting (5 vs 0).
- Each **game** = 200 rounds. Each **match** = 100 games.
- **Noise**: 5% chance each move is randomly flipped. Strategies must be robust to accidental defections.

## Strategy interface

Each strategy is a Python file at `examples/prisoners_dilemma/strategies/vN.py` exporting:

```python
def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    """Return True to cooperate, False to defect."""
```

- `my_history`: your previous moves (oldest first)
- `opp_history`: opponent's previous moves (oldest first)
- Both lists are empty on round 1
- Return `True` = cooperate, `False` = defect

## Workflow

Each iteration:

1. **Check standings**:
   ```
   uv run tracker.py leaderboard --db examples/prisoners_dilemma/matches.json
   ```

2. **Pick opponent** — always use `suggest`, don't cherry-pick:
   ```
   uv run tracker.py suggest vCurrent --db examples/prisoners_dilemma/matches.json
   ```

3. **Analyze**: Read the losing strategy and the opponent. Use `--trace` to see move-by-move replays:
   ```
   uv run examples/prisoners_dilemma/arena.py vNew vOld --trace --seed 42
   ```

4. **Create new strategy**: Write `examples/prisoners_dilemma/strategies/vN.py`. Name sequentially: v1, v2, v3, ...

5. **Benchmark and record** in one step with `--record`:
   ```
   uv run examples/prisoners_dilemma/arena.py vNew vOld --games 100 --record
   ```
   Or without `--record`, copy the printed `tracker.py record` command.

6. **Test against at least 3 opponents** before drawing conclusions. Versions with fewer opponents are flagged with `?` on the leaderboard. Use `suggest` each time to pick the most informative matchup.

7. **Repeat**.

## Classical strategies (reference)

These are well-known IPD strategies. Use them as inspiration, but don't just copy — the best evolved strategies often combine ideas.

- **Tit-for-Tat**: Cooperate first, then copy opponent's last move. Simple, effective, but fragile to noise.
- **Generous Tit-for-Tat**: Like TFT, but forgive defections ~10% of the time. Handles noise better.
- **Pavlov (Win-Stay, Lose-Shift)**: Repeat last move if it scored ≥3, otherwise switch. Self-correcting.
- **Grudger (Grim Trigger)**: Cooperate until opponent defects, then defect forever. Punishing but inflexible.
- **Tit-for-Two-Tats**: Only retaliate after two consecutive defections. Very forgiving.
- **Adaptive**: Track opponent's cooperation rate, cooperate if above threshold.
- **Prober**: Defect on rounds 2-3 to test opponent, then play TFT or exploit.

## Mutation guidelines

When creating a new version:

1. **Diagnose first**: Why did the parent lose? Common failure modes:
   - Too cooperative → exploited by defectors
   - Too aggressive → mutual defection spirals (1,1 per round)
   - No forgiveness → noise causes permanent retaliation chains
   - Too predictable → opponent can model and exploit

2. **Target one weakness**: Don't rewrite from scratch. Make a focused change.

3. **Test against variety**: A strategy that beats one opponent but loses to others isn't progress. Benchmark against at least 2-3 opponents.

4. **Think about noise**: With 5% flip rate, ~10 moves per 200-round game will be noisy. Strategies that can't recover from accidental defections will spiral into mutual punishment.

## Tips

- The best strategies tend to be **nice** (cooperate first), **retaliatory** (punish defection), **forgiving** (return to cooperation), and **non-envious** (don't try to outscore the opponent).
- Score per round: mutual C = 3.0, mutual D = 1.0. Anything above ~2.5 mean is good.
- With noise, pure tit-for-tat averages ~2.3. Forgiving variants reach ~2.7+.
- Don't optimize for beating one specific opponent — optimize for the field.
