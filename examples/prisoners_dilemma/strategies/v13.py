"""v13 — Gradual with noise detection.

Like v11 (Gradual) but with a noise filter: if we're in a cooperation
streak (both cooperated for the last 4+ rounds) and opponent defects once,
assume it's noise and don't trigger punishment. Only trigger punishment
when a defection occurs outside of a cooperation streak.

This should prevent the escalation death spirals that hurt v11 vs TFT
while keeping proportional punishment against real defectors.
"""

STREAK_THRESHOLD = 4


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
            # FREE state
            if not opp_history[i]:
                # Check if we were in a cooperation streak before this defection
                if i >= STREAK_THRESHOLD:
                    # Check that both players cooperated in the preceding window
                    my_recent = my_history[i - STREAK_THRESHOLD : i]
                    opp_recent = opp_history[i - STREAK_THRESHOLD : i]
                    if all(my_recent) and all(opp_recent):
                        # Likely noise — skip this defection
                        continue

                defection_count += 1
                punish_remaining = defection_count

    if punish_remaining > 0:
        return False
    return True
