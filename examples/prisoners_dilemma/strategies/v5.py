"""v5 — Forgiving Tit-for-Two-Tats + cooperation rate tracking.

Only retaliates after two consecutive defections (robust to noise).
Also tracks opponent's overall cooperation rate — if it drops below 40%,
switches to permanent defection.
"""


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if len(opp_history) < 2:
        return True

    # If opponent's overall cooperation rate is very low, defect
    coop_rate = sum(opp_history) / len(opp_history)
    if coop_rate < 0.40:
        return False

    # Tit-for-two-tats: only defect if opponent defected twice in a row
    if not opp_history[-1] and not opp_history[-2]:
        return False

    return True
