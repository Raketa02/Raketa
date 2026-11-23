"""A booked For-fun game's Social vibe, as the pairing draws it (#835;
``docs/adr/0207`` §5, §6): the table's number and the reader's rows.

The arithmetic is the Match Fit engine's and the tags that don't count are the
Player profile's; what is the court's own is **who the table is** — everybody
on it — and **the rows**: the reader's tags in the vocabulary's order, each
carried in the reader's direction — the reader, their side, then the other.
"""

from __future__ import annotations

import pytest

from app.kernel import InvariantViolated
from app.modules.games.domain.lineup import GameSide, LineUp, Seating
from app.modules.games.domain.vibe import CourtVibe, VibeRow, court_vibe_of
from app.modules.player_profile.domain.social_tags import SocialTag
from app.shared.ids import new_uuid

OLA, ANIA, MAREK, ZOFIA = (new_uuid() for _ in range(4))

DRINK = SocialTag.STAYS_FOR_A_DRINK
LAUGHS = SocialTag.LAUGHS_OFF_MISTAKES
MEET = SocialTag.HERE_TO_MEET_PLAYERS
SOMEONE = SocialTag.OPEN_TO_MEET_SOMEONE
NEW_IN_TOWN = SocialTag.NEW_IN_TOWN
QUIET = SocialTag.QUIET_AND_FOCUSED
HOME = SocialTag.STRAIGHT_HOME_AFTER

#: The 22% table: Ola {drink, laughs, meet, new in town, 💘}, Ania {drink, 💘},
#: Marek {laughs, meet}, Zofia {quiet, home}.
TAGS = {
    OLA: {NEW_IN_TOWN, SOMEONE, MEET, LAUGHS, DRINK},
    ANIA: {SOMEONE, DRINK},
    MAREK: {LAUGHS, MEET},
    ZOFIA: {QUIET, HOME},
}


def _court(side_a, side_b) -> LineUp:
    return LineUp.of(
        (
            *(Seating(side=GameSide.A, player_id=one) for one in side_a),
            *(Seating(side=GameSide.B, player_id=one) for one in side_b),
        )
    )


#: Zofia and Ania on side A, Marek and Ola on side B — so the court's own order
#: is not any reader's direction.
COURT = _court((ZOFIA, ANIA), (MAREK, OLA))


def test_the_number_is_the_whole_court_s_and_the_rows_the_reader_s():
    vibe = court_vibe_of(COURT, OLA, TAGS)

    assert vibe == CourtVibe(
        pct=22,
        rows=(
            VibeRow(tag=DRINK, carried_by=(OLA, ANIA)),
            VibeRow(tag=LAUGHS, carried_by=(OLA, MAREK)),
            VibeRow(tag=MEET, carried_by=(OLA, MAREK)),
            # 💘 is drawn, carried by Ania too, and counted nowhere above.
            VibeRow(tag=SOMEONE, carried_by=(OLA, ANIA)),
            VibeRow(tag=NEW_IN_TOWN, carried_by=(OLA,)),
        ),
    )


def test_the_carriers_are_named_in_the_reader_s_direction():
    """The reader, then their side, then the other — each side in the court's
    own order — as a game's details name a card's: the reader, ``sides.yours``,
    ``sides.theirs``."""

    everybody = {player: {DRINK} for player in (OLA, ANIA, MAREK, ZOFIA)}

    marek = court_vibe_of(COURT, MAREK, everybody)
    ania = court_vibe_of(COURT, ANIA, everybody)

    assert marek is not None and ania is not None
    assert marek.pct == ania.pct == 100
    assert marek.rows == (VibeRow(tag=DRINK, carried_by=(MAREK, OLA, ZOFIA, ANIA)),)
    assert ania.rows == (VibeRow(tag=DRINK, carried_by=(ANIA, ZOFIA, MAREK, OLA)),)


def test_every_reader_reads_one_number_and_their_own_rows():
    zofia = court_vibe_of(COURT, ZOFIA, TAGS)

    # The vocabulary's order, not the picker's: *Straight home after* first.
    assert zofia == CourtVibe(
        pct=22,
        rows=(
            VibeRow(tag=HOME, carried_by=(ZOFIA,)),
            VibeRow(tag=QUIET, carried_by=(ZOFIA,)),
        ),
    )


def test_somebody_whose_tags_are_not_known_carries_none_and_is_still_at_the_table():
    """Three of four known: Ola's three shared tags are each carried by one of
    the *three* others, so the unknown fourth still divides."""

    known = {OLA: TAGS[OLA], ANIA: TAGS[ANIA], MAREK: TAGS[MAREK]}

    vibe = court_vibe_of(COURT, OLA, known)

    assert vibe is not None
    assert vibe.pct == 29  # (1 + ⅓ + ⅔) over 7 carryings


def test_singles_is_the_plain_overlap_of_the_two():
    court = _court((OLA,), (MAREK,))

    vibe = court_vibe_of(court, OLA, TAGS)

    # Twice the two they share, over the six the two carry (💘 aside).
    assert vibe is not None and vibe.pct == 67


def test_nothing_is_drawn_while_nobody_holds_a_tag_that_counts():
    only_hearts = {player: {SOMEONE} for player in (OLA, ANIA, MAREK, ZOFIA)}

    assert court_vibe_of(COURT, OLA, only_hearts) is None
    assert court_vibe_of(COURT, OLA, {}) is None


def test_a_reader_off_the_court_is_a_broken_precondition():
    stranger = new_uuid()

    with pytest.raises(InvariantViolated):
        court_vibe_of(COURT, stranger, TAGS)


def test_a_court_with_a_seat_open_is_a_broken_precondition():
    """The pairing never draws a vibe on a court somebody has left
    (``docs/adr/0162`` §3), so asking for one is a wrong branch."""

    with pytest.raises(InvariantViolated):
        court_vibe_of(COURT.vacated_by(ZOFIA), OLA, TAGS)
