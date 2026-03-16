"""v16 — Gradual with amnesty.

Like v11 (Gradual) but resets the defection counter after 20 rounds of
mutual cooperation in FREE state. This prevents noise accumulation from
causing 10+ round punishment chains late in the game, which devastates
against TFT. Amnesty keeps punishment proportional to recent behavior.
"""

AMNESTY_THRESHOLD = 20


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True

    defection_count = 0
    punish_remaining = 0
    peace_remaining = 0
    free_coop_streak = 0

    for i in range(len(opp_history)):
        if punish_remaining > 0:
            punish_remaining -= 1
            free_coop_streak = 0
            if punish_remaining == 0:
                peace_remaining = 2
        elif peace_remaining > 0:
            peace_remaining -= 1
            free_coop_streak = 0
        else:
            # FREE state
            if not opp_history[i]:
                defection_count += 1
                punish_remaining = defection_count
                free_coop_streak = 0
            else:
                free_coop_streak += 1
                if free_coop_streak >= AMNESTY_THRESHOLD:
                    defection_count = 0
                    free_coop_streak = 0

    if punish_remaining > 0:
        return False
    return True
