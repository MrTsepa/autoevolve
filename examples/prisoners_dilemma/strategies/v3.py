"""v3 — Generous Tit-for-Tat. Like TFT but forgives defections ~10% of the time."""

import random


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True
    if opp_history[-1]:
        return True
    # Opponent defected — forgive with 10% probability
    return random.random() < 0.10
