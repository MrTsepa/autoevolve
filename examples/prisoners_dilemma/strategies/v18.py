"""v18 — Gradual with cooldown.

Like v11 (Gradual) but adds a 3-round cooldown after each punishment+peace
cycle. During cooldown, opponent defections are ignored (no new punishment
triggered). This prevents the escalation feedback loop where TFT mirrors
our punishment D, Gradual detects it as a new defection in FREE state,
triggers more punishment, which TFT mirrors again, etc.
"""

COOLDOWN = 3


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True

    defection_count = 0
    punish_remaining = 0
    peace_remaining = 0
    cooldown_remaining = 0

    for i in range(len(opp_history)):
        if punish_remaining > 0:
            punish_remaining -= 1
            if punish_remaining == 0:
                peace_remaining = 2
        elif peace_remaining > 0:
            peace_remaining -= 1
            if peace_remaining == 0:
                cooldown_remaining = COOLDOWN
        elif cooldown_remaining > 0:
            cooldown_remaining -= 1
        else:
            # FREE state — detect defections
            if not opp_history[i]:
                defection_count += 1
                punish_remaining = defection_count

    if punish_remaining > 0:
        return False
    return True
