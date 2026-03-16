"""v19 — Gradual with retaliation filter.

Like v11 (Gradual) but with a critical fix: in FREE state, only count
opponent defections when OUR previous move was cooperation. If we defected
last round (noise, punishment leak, etc.), opponent's defection is likely
retaliation and shouldn't trigger new punishment.

This breaks the feedback loop: noise flips our C→D, TFT mirrors back D,
but we DON'T count that as a new defection because we defected first.
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
            # FREE state — only count unprovoked defections
            if not opp_history[i]:
                # Was my previous move a cooperation? (provoked vs unprovoked)
                provoked = i > 0 and not my_history[i - 1]
                if not provoked:
                    defection_count += 1
                    punish_remaining = defection_count

    if punish_remaining > 0:
        return False
    return True
