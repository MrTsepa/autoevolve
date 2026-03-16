"""v8 — Gradual with TFT fallback.

Starts with Gradual. After 5+ observed defections, checks mirroring rate.
If ≥ 70%, classifies opponent as TFT and switches to TFT mode (mirror
opponent's last move). This avoids both:
- Gradual's escalation feedback loop against mirrors
- Always-cooperate's vulnerability to noise (free DC=5 for opponent)

Against non-mirrors: continues with Gradual escalation.
"""


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True

    n = len(my_history)

    # Check if opponent is a mirror (TFT-like)
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
            # Detected TFT — play TFT (mirror, don't just cooperate)
            return opp_history[-1]

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
