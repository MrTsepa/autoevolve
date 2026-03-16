"""v4 — Gradual (Beaufils et al. 1996). Proportional punishment.

Cooperates initially. On the Nth opponent defection (detected in FREE state),
punishes with N consecutive defections then 2 cooperations (peace signal).
Ignores opponent defections during punishment/peace phases.
"""


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True

    defection_count = 0
    punish_remaining = 0
    peace_remaining = 0

    for i in range(len(opp_history)):
        if punish_remaining > 0:
            punish_remaining -= 1
            if punish_remaining == 0:
                peace_remaining = 2
        elif peace_remaining > 0:
            peace_remaining -= 1
        else:
            if not opp_history[i]:
                defection_count += 1
                punish_remaining = defection_count

    if punish_remaining > 0:
        return False
    return True
