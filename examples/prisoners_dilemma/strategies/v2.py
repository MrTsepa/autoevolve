"""v2 — Tit-for-Tat. Cooperate first, then copy opponent's last move."""


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True
    return opp_history[-1]
