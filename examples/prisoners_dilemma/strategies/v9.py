"""v9 — Soft Pavlov. Pavlov with stochastic forgiveness.

Standard Pavlov (win-stay, lose-shift), but with 15% chance of
cooperating after bad outcomes instead of switching. Adds noise
tolerance without a deterministic buffer that can be exploited.
"""

import random


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not my_history:
        return True

    my_last = my_history[-1]
    opp_last = opp_history[-1]

    # Good outcome: opponent cooperated (CC=3 or DC=5)
    good = opp_last

    if good:
        return my_last  # win-stay

    # Bad outcome — standard Pavlov switches, but we forgive 15% of the time
    if random.random() < 0.15:
        return my_last  # stay (forgive)

    return not my_last  # lose-shift
