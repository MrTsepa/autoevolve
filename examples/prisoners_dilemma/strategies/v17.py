"""v17 — Gradual with in-game mirror detection.

Uses Gradual proportional punishment as base. During/after punishment phases,
tracks whether the opponent mirrors our defections (with 1-round lag). If
mirroring rate ≥ 80% after 10+ observations, switches to always-cooperate
for the rest of the game (optimal against TFT-like opponents).

This should beat Pavlov (via Gradual punishment) while not losing to TFT
(via cooperative switch once TFT is detected).
"""

MIRROR_MIN_OBS = 10
MIRROR_THRESHOLD = 0.80


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True

    n = len(opp_history)

    # Check mirror detection: does opponent copy my moves with 1-round lag?
    if n >= MIRROR_MIN_OBS:
        mirror_matches = 0
        mirror_checks = 0
        for i in range(1, n):
            mirror_checks += 1
            if opp_history[i] == my_history[i - 1]:
                mirror_matches += 1
        if mirror_checks >= MIRROR_MIN_OBS:
            mirror_rate = mirror_matches / mirror_checks
            if mirror_rate >= MIRROR_THRESHOLD:
                return True  # Detected TFT — cooperate

    # Gradual punishment logic
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
