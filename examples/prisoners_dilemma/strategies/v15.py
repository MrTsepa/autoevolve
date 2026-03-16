"""v15 — TFT with DD-escape.

Plays TFT (mirror opponent's last move) with one exception:
after mutual defection (both defected last round), cooperate
instead of mirroring. This breaks DD spirals that TFT can't
escape, giving the same advantage Pavlov has.
"""


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True

    my_last = my_history[-1]
    opp_last = opp_history[-1]

    # DD escape: if both defected, cooperate to break the spiral
    if not my_last and not opp_last:
        return True

    # Otherwise: TFT — mirror opponent's last move
    return opp_last
