"""v8 — Buffered Pavlov. Standard Pavlov with a noise buffer.

During cooperation streaks (5+ rounds of mutual cooperation), a single
bad outcome is assumed to be noise and ignored. This prevents Pavlov
from accidentally learning to exploit a cooperating partner due to noise.
"""


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not my_history:
        return True

    my_last = my_history[-1]
    opp_last = opp_history[-1]

    # Standard Pavlov: good outcome (≥3) = stay, bad = switch
    # Good: CC(3) or DC(5). Bad: CD(0) or DD(1).
    good = opp_last  # equivalent: good iff opponent cooperated

    # Noise buffer: if we had a cooperation streak before this round,
    # treat a single bad outcome as noise
    if not good and len(my_history) >= 5:
        recent_mine = my_history[-5:]
        recent_opp = opp_history[-5:-1]  # exclude current bad round
        if all(recent_mine) and all(recent_opp):
            # We were in a cooperation streak — this is likely noise, forgive
            return True

    if good:
        return my_last
    return not my_last
