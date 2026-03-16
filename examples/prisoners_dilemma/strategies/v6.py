"""v6 — Sliding Window TFT. TFT base with noise-aware forgiveness.

Uses a 10-round sliding window: if opponent cooperated ≥60% recently,
forgive a single defection (likely noise). Otherwise, mirror strictly.
"""

import random

WINDOW = 10
FORGIVE_THRESHOLD = 0.60
FORGIVE_PROB = 0.30


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True

    # Opponent cooperated last round — cooperate
    if opp_history[-1]:
        return True

    # Opponent defected last round — should we forgive?
    recent = opp_history[-WINDOW:]
    if len(recent) >= 3:
        recent_coop_rate = sum(recent) / len(recent)
        if recent_coop_rate >= FORGIVE_THRESHOLD:
            # Likely noise — forgive with probability
            return random.random() < FORGIVE_PROB

    # Otherwise, retaliate
    return False
