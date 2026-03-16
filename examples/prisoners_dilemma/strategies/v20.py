"""v20 — Gradual-Pavlov hybrid.

Uses Gradual's proportional punishment with Pavlov's DD-escape.
The key addition: if both players defected last round (DD state),
override the punishment schedule and cooperate. This breaks mutual
defection spirals that devastate Gradual vs TFT.

The punishment resumes after the escape attempt.
"""


def strategy(my_history: list[bool], opp_history: list[bool]) -> bool:
    if not opp_history:
        return True

    # DD escape: override everything if both defected last round
    if len(my_history) >= 1 and not my_history[-1] and not opp_history[-1]:
        return True

    # Gradual punishment logic
    defection_count = 0
    punish_remaining = 0
    peace_remaining = 0

    for i in range(len(opp_history)):
        # Check if we would have used DD-escape at this round
        if i > 0 and not my_history[i - 1] and not opp_history[i - 1]:
            # We cooperated (DD-escape) — don't count this round for state machine
            # But we still need to advance the punishment counter
            if punish_remaining > 0:
                punish_remaining -= 1
                if punish_remaining == 0:
                    peace_remaining = 2
            elif peace_remaining > 0:
                peace_remaining -= 1
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
