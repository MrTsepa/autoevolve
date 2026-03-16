"""v5 — Gradual with decaying counter.

Like Gradual (v4) but the defection counter decays by 1 after each
punishment+peace cycle completes. This prevents noise from compounding
forever — late-game punishments stay proportional to *recent* behavior
rather than all-time accumulated noise events.
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
            if peace_remaining == 0:
                # Cycle complete — decay the counter
                defection_count = max(0, defection_count - 1)
        else:
            if not opp_history[i]:
                defection_count += 1
                punish_remaining = defection_count

    if punish_remaining > 0:
        return False
    return True
