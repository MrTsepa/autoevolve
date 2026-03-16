"""v14 — Mirror Detector + Gradual.

After a probe phase (15 rounds), classifies the opponent:
- If opponent mirrors my moves (TFT-like): always cooperate (CC=3 is optimal)
- Otherwise: use Gradual proportional punishment

Mirror detection: check if opp_history[i] == my_history[i-1] for ≥70% of rounds.
"""

PROBE_ROUNDS = 15
MIRROR_THRESHOLD = 0.70


def _is_mirror(my_history, opp_history):
    """Check if opponent is mirroring our moves with 1-round lag."""
    if len(my_history) < PROBE_ROUNDS:
        return False
    matches = 0
    checks = 0
    for i in range(1, len(opp_history)):
        if opp_history[i] == my_history[i - 1]:
            matches += 1
        checks += 1
    return checks > 0 and matches / checks >= MIRROR_THRESHOLD


def _gradual_move(opp_history, my_history):
    """Compute the Gradual strategy move."""
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
                punish_remaining = defection_count

    if punish_remaining > 0:
        return False
    return True


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True

    # During probe phase, play TFT (gives mirror detectable pattern)
    if len(opp_history) < PROBE_ROUNDS:
        return opp_history[-1] if opp_history else True

    # After probe phase, classify and adapt
    if _is_mirror(my_history, opp_history):
        return True  # Cooperate with TFT-like opponents

    return _gradual_move(opp_history, my_history)
