"""v10 — Adaptive Pavlov. Detects opponent type via sliding window and adapts.

- Against cooperators (>70% coop in last 20 rounds): cooperate (stay in CC)
- Against defectors (<30% coop): defect (don't get exploited)
- In between: Soft Pavlov (win-stay, lose-shift with 15% forgiveness)
"""

import random

WINDOW = 20


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not my_history:
        return True

    # Calculate opponent's recent cooperation rate
    recent = opp_history[-WINDOW:]
    coop_rate = sum(recent) / len(recent) if recent else 1.0

    # Cooperative opponent — just cooperate (avoids spirals with TFT)
    if coop_rate > 0.70:
        return True

    # Hostile opponent — defect
    if coop_rate < 0.30:
        return False

    # Mixed behavior — Soft Pavlov
    my_last = my_history[-1]
    opp_last = opp_history[-1]
    good = opp_last  # CC or DC

    if good:
        return my_last

    if random.random() < 0.15:
        return my_last

    return not my_last
