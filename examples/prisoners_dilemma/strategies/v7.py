"""v7 — Optimal Generous TFT with adaptive forgiveness.

Forgives defections at ~33% (theoretically optimal for 5% noise).
But tracks overall cooperation rate and reduces forgiveness against
persistent defectors.
"""

import random


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True

    # Opponent cooperated — always cooperate back
    if opp_history[-1]:
        return True

    # Opponent defected — calculate forgiveness rate
    n = len(opp_history)
    coop_rate = sum(opp_history) / n

    # Base forgiveness: 33% (optimal for this payoff matrix with 5% noise)
    # Scale down as opponent becomes more defective
    if coop_rate > 0.7:
        forgive = 0.33
    elif coop_rate > 0.5:
        forgive = 0.20
    elif coop_rate > 0.3:
        forgive = 0.10
    else:
        forgive = 0.0

    return random.random() < forgive
