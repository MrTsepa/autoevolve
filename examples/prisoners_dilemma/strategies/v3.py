"""v3 — Pavlov (Win-Stay, Lose-Shift). Repeat last move if it scored ≥3, otherwise switch."""


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not my_history:
        return True
    # Good outcome: opponent cooperated (CC=3, DC=5)
    # Bad outcome: opponent defected (CD=0, DD=1)
    good = opp_history[-1]
    if good:
        return my_history[-1]  # stay
    return not my_history[-1]  # shift
