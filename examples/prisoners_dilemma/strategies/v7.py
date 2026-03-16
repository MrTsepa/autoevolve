"""v7 — Gradual with auto-classification.

Starts with Gradual. Tracks rounds where we defected and whether the
opponent mirrored (defected next round). After 5+ defection observations,
if mirroring rate ≥ 70%, classifies opponent as TFT and switches to
always-cooperate permanently. This avoids the punishment feedback loop
that costs Gradual 5 points per noise event against mirrors.
"""


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True

    n = len(my_history)

    # Check if opponent is a mirror (TFT-like)
    # Count: when I defected, did opponent defect next round?
    mirror_hits = 0
    mirror_checks = 0
    for i in range(n - 1):
        if not my_history[i]:  # I defected on round i
            mirror_checks += 1
            if not opp_history[i + 1]:  # opponent defected on round i+1
                mirror_hits += 1

    if mirror_checks >= 5:
        mirror_rate = mirror_hits / mirror_checks
        if mirror_rate >= 0.70:
            return True  # Detected TFT — cooperate forever

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
