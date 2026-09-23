"""What this context refuses, and why each refusal is a refusal and not a no-op.

Three families, and each is a different person's mistake.

**Whose game is this.** One code covers a game that does not exist, a game
somebody else played and a game whose result has not settled, and that merge is
deliberate — it is ``games``' own argument, that separating them would answer *is
this id real* about four strangers' evening. Nobody legitimately reaches it: the
card is drawn from a read that only lists games this player may rate, so arriving
here is a stale screen or a race, and every one of those has the same remedy.

**Who is on the card.** A subject who was not on that court, and the same person
named twice, are both a client sending a card the platform did not draw. They are
refused rather than dropped, because a silently discarded rating is one the
player believes they gave.

**What a star is.** One to five, whole. It is refused here rather than bounded on
the wire so that the range has exactly one home — a second copy in a Pydantic
field would be the first thing to drift, and the domain's copy would then be
unreachable through the only route that reaches it.

**No refusal here names anybody and none carries a payload**, on this
repository's standing rule. There is nothing to disclose about a court the
refused player was on, and the rule is kept so that it stays a rule.
"""

from __future__ import annotations

from app.shared.domain.errors import BadRequestError, ConflictError, ForbiddenError


class ThisGameIsNotYoursToRate(ForbiddenError):
    """No settled game of **yours** has that id.

    **One code for three cases** — it does not exist, you did not play in it, or
    its result has not settled yet — because the remedy is the same for all
    three and separating them would answer *is this id real* about somebody
    else's evening. It is ``games``' rule, applied by the context that reads
    ``games``' courts.

    Its own code and not ``games``' ``you_were_not_on_this_court``, because it is
    not the same fact: that one is about acting on a result and this one folds in
    *has it settled*, which is the opposite of what that route refuses on.
    """

    code = "this_game_is_not_yours_to_rate"

    def __init__(self) -> None:
        super().__init__("There is no settled game of yours with that id.")


class YouHaveAlreadyRatedThisGame(ConflictError):
    """A second card for one game.

    **Submitting closes the card, and a blank stays blank for ever.** This is the
    refusal that makes both true: without it a player could come back and fill in
    the person they left out, and *I am not rating anyone* would stop being an
    answer and start being a delay. It fires for the all-blank card too — an
    explicit refusal to rate is an answer, and an answer is what closes a card.
    """

    code = "you_have_already_rated_this_game"

    def __init__(self) -> None:
        super().__init__("You have already answered this game's card.")


class TheyWereNotOnThisCourt(BadRequestError):
    """Stars for somebody who was not there — **including yourself.**

    You rate everybody else who was on the court and nobody else: in doubles both
    opponents and your partner, in singles the one opponent. Rating yourself is
    the same refusal rather than one of its own, because *everybody else* is one
    rule and a second class would be a second place for it to be true.

    A refusal rather than a dropped row: a rating quietly discarded is a rating
    the player believes they gave, about a person they cannot check.
    """

    code = "they_were_not_on_this_court"

    def __init__(self) -> None:
        super().__init__("You can only rate the other players on that court.")


class YouRatedTheSamePersonTwice(BadRequestError):
    """Two answers about one person on one card.

    Refused rather than collapsed, because collapsing means the platform choosing
    which of somebody's two opinions to keep — and it would choose by whichever
    order the request happened to arrive in.
    """

    code = "you_rated_the_same_person_twice"

    def __init__(self) -> None:
        super().__init__("One card carries one answer about each player.")


class StarsAreOneToFive(BadRequestError):
    """A number that is not a tap on one of five stars.

    **No zero**, deliberately: a rating that reads as *worthless* is a weapon out
    of proportion to a tap, and one star already dents an average about as hard.
    **No halves**, deliberately: five taps, one number.

    A refusal and not an ``invariant``, on ``games``' rule for a score — a star
    count arrives from a person tapping it, so a bad one is somebody's client
    sending the wrong thing rather than a broken precondition, and answering it
    with a 500 would be answering a tap with an outage.
    """

    code = "stars_are_one_to_five"

    def __init__(self) -> None:
        super().__init__("A rating is one to five whole stars.")
