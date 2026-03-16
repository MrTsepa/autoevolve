"""v9 — Gradual with faster TFT detection.

Like v8 but lowers classification threshold from 5 to 3 observed defections.
This triggers TFT mode after ~2 punishment cycles instead of ~3-4, reducing
the early-game damage against mirrors.

Also lowers the mirroring threshold from 70% to 60% to be more forgiving
of noise during classification.
"""


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True

    n = len(my_history)

    # Check if opponent is a mirror (TFT-like)
    mirror_hits = 0
    mirror_checks = 0
    for i in range(n - 1):
        if not my_history[i]:
            mirror_checks += 1
            if not opp_history[i + 1]:
                mirror_hits += 1

    if mirror_checks >= 3:
        mirror_rate = mirror_hits / mirror_checks
        if mirror_rate >= 0.60:
            return opp_history[-1]  # TFT mode

    # Default: Gradual
    defection_count = 0
    punish_remaining = 0
    peace_remaining = 0

    for i in range(n):
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
