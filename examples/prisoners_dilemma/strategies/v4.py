"""v4 — Pavlov (Win-Stay, Lose-Shift). Repeat last move if it scored ≥3, otherwise switch."""


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not my_history:
        return True
    # Did I score well last round? (CC=3, DC=5 are good; CD=0, DD=1 are bad)
    my_last = my_history[-1]
    opp_last = opp_history[-1]
    good_outcome = (my_last and opp_last) or (not my_last and opp_last)
    # If good outcome, stay; if bad, shift
    if good_outcome:
        return my_last
    return not my_last
