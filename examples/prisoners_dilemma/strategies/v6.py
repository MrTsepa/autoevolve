"""v6 — Probe + Classify + Gradual.

Probes on rounds 5-6 to classify the opponent:
- TFT-like (mirrors): defects on both rounds 6 AND 7 → cooperate forever
- Pavlov-like: defects on 6 but cooperates on 7 (DD→switch) → use Gradual
- Other: use Gradual

Against TFT, this avoids the punishment feedback loop entirely (CC=3 forever).
Against Pavlov, escalating Gradual punishment still works.
"""

PROBE_ROUNDS = {4, 5}  # 0-indexed: rounds 5-6


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    n = len(my_history)

    # Rounds 0-3: cooperate (establish baseline)
    if n < 4:
        return True

    # Rounds 4-5: probe (defect)
    if n in PROBE_ROUNDS:
        return False

    # Round 6: cooperate (absorb retaliation)
    if n == 6:
        return True

    # Round 7+: classify and adapt
    if n >= 7:
        # Check opponent's response to our probe defections (rounds 4-5)
        # TFT mirrors with 1-round lag: defects on rounds 5 AND 6
        # Pavlov: defects on 5 (CD→switch to D), cooperates on 6 (DD→switch to C)
        opp_r5 = opp_history[5]  # response to our defection on round 4
        opp_r6 = opp_history[6]  # response to our defection on round 5

        is_mirror = not opp_r5 and not opp_r6  # both defections = mirror

        if is_mirror:
            # Cooperate forever — no punishment needed
            return True

        # Non-mirror: use Gradual (ignoring probe rounds)
        return _gradual(opp_history, n)

    return True


def _gradual(opp_history, n):
    """Gradual punishment, skipping the probe phase."""
    defection_count = 0
    punish_remaining = 0
    peace_remaining = 0

    for i in range(len(opp_history)):
        # Skip probe phase and its aftermath (rounds 0-7)
        if i < 8:
            continue

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
