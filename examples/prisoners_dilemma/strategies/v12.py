"""v12 — Capped Gradual. Like v11 but caps punishment at 3 rounds.

Without the cap, noise accumulation causes punishment to escalate to 10+
rounds, which devastates against mirror strategies (TFT). The cap of 3
still punishes defectors effectively while preventing runaway spirals.
"""

MAX_PUNISH = 3


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
                punish_remaining = min(defection_count, MAX_PUNISH)

    if punish_remaining > 0:
        return False
    return True
