"""A game still filling, opened by anybody dealt it — the pure rules (#542; the
mechanics §14.2; the screens A4.2).

**Who is drawn**: for a reader still deciding, their own card — everybody In,
them, the rest of their version — exactly as the deck deals it, and withheld as
the deck withholds it when somebody In is somebody they do not fit. For a reader
In, everybody In and the open seats: nobody else's deciding is shown to them.

**The status** is *filling* until every seat is In; a full game still filling is
one an On request club has to confirm — *waiting for the club*. **The actions**
are the reader's: *I'm in* and *Not this time* while they may answer, *Withdraw*
when they are In, *Leave the game* while the club decides, and nothing once the
game is over or their answer is final.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, instant
from app.modules.proposals.domain.details import (
    ProposalStatus,
    ReaderAction,
    actions_for,
    details_view,
    status_of_proposal,
)
from app.modules.player_profile.domain.gender import Gender
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.post import Who, stand_together
from app.modules.proposals.domain.proposal import Origin, Proposal, ReopenReason

WARSAW = ZoneInfo("Europe/Warsaw")
MADE_AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
NOW = MADE_AT + timedelta(hours=1)
START = instant(datetime(2026, 10, 10, 17, tzinfo=WARSAW))
BOOK_BY = START - timedelta(hours=2)

ME, A, B, C, D, E = (uuid4() for _ in range(6))
EVERYBODY = frozenset({ME, A, B, C, D, E})


def a_pick(*versions: tuple[UUID, ...]) -> Proposal:
    proposal = Proposal.make(
        proposal_id=uuid4(),
        pool=Pool(id=uuid4(), kind=PoolKind.GROUP),
        origin=Origin.PICK,
        poster_id=None,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        club_id=uuid4(),
        start=START,
        share_grosze=30_00,
        book_by=BOOK_BY,
        at=MADE_AT,
    )
    for version in versions:
        proposal.deal(version, at=MADE_AT)
    return proposal


def a_post_of_mine(*versions: tuple[UUID, ...]) -> Proposal:
    proposal = Proposal.make(
        proposal_id=uuid4(),
        pool=Pool(id=uuid4(), kind=PoolKind.GROUP),
        origin=Origin.POST,
        poster_id=ME,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        club_id=uuid4(),
        start=START,
        share_grosze=30_00,
        book_by=BOOK_BY,
        at=MADE_AT,
    )
    for version in versions:
        proposal.deal(version, at=MADE_AT)
    return proposal


def unfit(*pairs: tuple[UUID, UUID]) -> frozenset[frozenset[UUID]]:
    return frozenset(frozenset(pair) for pair in pairs)


def view(proposal: Proposal, *, unfit=frozenset(), pool=EVERYBODY):
    return details_view(proposal, ME, unfit=unfit, in_the_pool=pool, now=NOW)


# --------------------------------------------------------------------------- #
# Who is drawn
# --------------------------------------------------------------------------- #


def test_a_reader_still_deciding_sees_their_own_card():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(B, at=NOW)

    seen = view(pick)

    assert seen is not None
    assert seen.in_ == (B,)
    assert seen.people == (B, ME, A, C)
    assert seen.beside_the_reader == (B, A, C)


def test_a_reader_in_sees_everybody_in_and_the_open_seats():
    """Nobody's deciding is shown to somebody In — *filled posters for everyone
    In, dashed empties for the open seats* (the screens A3.2)."""

    pick = a_pick((ME, A, B, C))
    pick.say_yes(A, at=NOW)
    pick.say_yes(ME, at=NOW)

    seen = view(pick)

    assert seen is not None
    assert seen.in_ == (A, ME)
    assert seen.people == (A, ME)
    assert seen.beside_the_reader == (A,)


def test_a_poster_sees_their_post_with_the_people_in():
    post = a_post_of_mine((A, B, C))
    post.say_yes(A, at=NOW)

    seen = view(post)

    assert seen is not None
    assert seen.people == (ME, A)


def test_a_name_the_reader_does_not_fit_is_left_off_their_card():
    pick = a_pick((ME, A, B, C))

    seen = view(pick, unfit=unfit((ME, B)))

    assert seen is not None
    assert seen.people == (ME, A, C)


def test_a_card_with_somebody_in_the_reader_does_not_fit_is_withheld():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(A, at=NOW)

    assert view(pick, unfit=unfit((ME, A))) is None


def test_somebody_never_dealt_it_is_not_shown_it():
    pick = a_pick((A, B, C, D))

    assert view(pick) is None


def test_a_reader_who_said_no_still_sees_what_they_said_no_to():
    pick = a_pick((ME, A, B, C))
    pick.say_no(ME, at=NOW)

    seen = view(pick)

    assert seen is not None
    assert ME in seen.people


def test_nobody_is_still_deciding_on_a_game_that_is_over():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(A, at=NOW)

    seen = details_view(pick, ME, unfit=frozenset(), in_the_pool=EVERYBODY, now=BOOK_BY)

    assert seen is not None
    assert seen.people == (A, ME)


# --------------------------------------------------------------------------- #
# The status
# --------------------------------------------------------------------------- #


def test_a_game_with_seats_open_is_filling():
    assert status_of_proposal(a_pick((ME, A, B, C)), now=NOW) is ProposalStatus.FILLING


def test_a_full_game_still_filling_waits_for_the_club():
    """At an On request club the fill leaves a full game untouched until the
    club says yes (#541, #543)."""

    pick = a_pick((ME, A, B, C))
    for player in (ME, A, B, C):
        pick.say_yes(player, at=NOW)

    assert status_of_proposal(pick, now=NOW) is ProposalStatus.WAITING_FOR_THE_CLUB


def test_a_game_past_its_book_by_is_expired_before_any_sweep():
    pick = a_pick((ME, A, B, C))

    assert status_of_proposal(pick, now=BOOK_BY) is ProposalStatus.EXPIRED


def test_a_filled_game_is_filled():
    pick = a_pick((ME, A, B, C))
    for player in (ME, A, B, C):
        pick.say_yes(player, at=NOW)
    pick.fill(first_side=(ME, A), second_side=(B, C), by=C, at=NOW)

    assert status_of_proposal(pick, now=NOW) is ProposalStatus.FILLED


# --------------------------------------------------------------------------- #
# The reader's actions
# --------------------------------------------------------------------------- #


def test_a_reader_still_deciding_may_say_yes_or_no():
    pick = a_pick((ME, A, B, C))

    assert actions_for(pick, ME, now=NOW) == (ReaderAction.YES, ReaderAction.NO)


def test_a_reader_in_may_withdraw():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(ME, at=NOW)

    assert actions_for(pick, ME, now=NOW) == (ReaderAction.WITHDRAW,)


def test_while_the_club_decides_a_reader_in_may_only_leave():
    """*Withdraw* is hidden while waiting for the club; *Leave the game* with its
    sheet takes its place (the mechanics §13)."""

    pick = a_pick((ME, A, B, C))
    for player in (ME, A, B, C):
        pick.say_yes(player, at=NOW)

    assert actions_for(pick, ME, now=NOW) == (ReaderAction.LEAVE,)


def test_a_reader_who_withdrew_may_say_yes_again():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(ME, at=NOW)
    pick.withdraw_yes(ME, at=NOW)

    assert actions_for(pick, ME, now=NOW) == (ReaderAction.YES, ReaderAction.NO)


def test_a_no_is_final():
    pick = a_pick((ME, A, B, C))
    pick.say_no(ME, at=NOW)

    assert actions_for(pick, ME, now=NOW) == ()


def test_a_refused_payment_is_confirmed_rather_than_said_again():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(ME, at=NOW)
    pick.reopen_seat(
        ME, reason=ReopenReason.AUTHENTICATION_REQUIRED, seat_charge_id=uuid4(), at=NOW
    )

    assert actions_for(pick, ME, now=NOW) == (ReaderAction.CONFIRM_PAYMENT,)


def test_a_seat_reopened_for_the_terms_is_a_yes_to_say_again():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(ME, at=NOW)
    pick.reopen_seat(ME, reason=ReopenReason.TERMS_NEEDED, seat_charge_id=None, at=NOW)

    assert actions_for(pick, ME, now=NOW) == (ReaderAction.YES, ReaderAction.NO)


def test_a_seat_reopened_because_they_no_longer_fit_offers_nothing():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(ME, at=NOW)
    pick.reopen_seat(
        ME, reason=ReopenReason.NO_LONGER_FITS, seat_charge_id=None, at=NOW
    )

    assert actions_for(pick, ME, now=NOW) == ()


def test_a_paused_yes_comes_back_by_itself_and_offers_nothing():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(ME, at=NOW)
    pick.pause_yes(ME, at=NOW)

    assert actions_for(pick, ME, now=NOW) == ()


def test_a_full_game_offers_a_reader_outside_it_nothing():
    pick = a_pick((A, B, C, D), (ME,))
    for player in (A, B, C, D):
        pick.say_yes(player, at=NOW)

    assert actions_for(pick, ME, now=NOW) == ()


def test_a_game_that_is_over_offers_nothing():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(ME, at=NOW)

    assert actions_for(pick, ME, now=BOOK_BY) == ()


# --------------------------------------------------------------------------- #
# Mixed pairs (#546)
# --------------------------------------------------------------------------- #

GENDERS = {ME: Gender.MAN, A: Gender.MAN, B: Gender.MAN, C: Gender.WOMAN}


def two_of_each(people) -> bool:
    return stand_together(Who.MIXED_PAIRS, GENDERS, people, seats=4)


def test_a_reader_who_would_be_a_third_of_their_gender_sees_no_details():
    """The deck withholds the card from a third man, and its details are the
    same card."""

    pick = a_pick((ME, A, B, C))
    pick.say_yes(A, at=NOW)
    pick.say_yes(B, at=NOW)

    assert (
        details_view(
            pick,
            ME,
            unfit=frozenset(),
            in_the_pool=EVERYBODY,
            now=NOW,
            may_stand=two_of_each,
        )
        is None
    )


def test_a_name_a_mixed_game_has_no_seat_for_is_left_off_the_details():
    pick = a_pick((ME, A, B, C))
    pick.say_yes(C, at=NOW)

    seen = details_view(
        pick,
        ME,
        unfit=frozenset(),
        in_the_pool=EVERYBODY,
        now=NOW,
        may_stand=two_of_each,
    )

    assert seen is not None
    assert seen.others == (A,)
