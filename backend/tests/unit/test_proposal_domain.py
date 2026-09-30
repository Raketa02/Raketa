"""The Proposal aggregate — a game still filling, and the rules a seam further out
cannot see (#538; the mechanics §5–§7, ``docs/adr/0189`` §2, §5).

Five families, and each is a rule that would otherwise only be true by accident.

**Born made**: a proposal is a court hour at a club with a price fixed on it and
a book-by the club decided, and a **post** is the poster's yes from its first
event — posting is saying yes.

**Versions** are how one game is dealt to more people than it has seats: at most
three, each person in one, and never more people than the seats still open.

**Yeses are the game's, not a version's.** Two people on two versions who both
say yes are both In on the one game, which is what makes a game dealt in three
versions fill when three versions' worth of yeses would not.

**A yes and a no are silent, and a no is final**: a card swiped left never comes
back, and a yes taken back is a seat handed on — neither can be answered again.

**The only deadline is the book-by**, and *expired* is read off the clock at
every instant; the record of it is written later, by whoever notices.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.engines.matchfit.core import SearchMode
from app.kernel import InvariantViolated, Sport, instant
from app.modules.proposals.domain.errors import (
    ProposalAlreadyAnswered,
    ProposalIsFull,
    ProposalIsOver,
    ProposalNotFound,
)
from app.modules.proposals.domain.events import (
    CourtHourLost,
    NoSaid,
    ProposalExpired,
    ProposalMade,
    ProposalWithdrawn,
    VersionDealt,
    YesSaid,
    YesWithdrawn,
)
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.proposal import (
    Origin,
    Proposal,
    Standing,
)

MADE_AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
START = instant(datetime(2026, 10, 10, 15, tzinfo=timezone.utc))
BOOK_BY = instant(datetime(2026, 10, 7, 15, tzinfo=timezone.utc))
LATER = MADE_AT + timedelta(hours=1)

MAREK, B, C, D, E, F, G, H = (uuid4() for _ in range(8))


def a_pick(sport: Sport = Sport.PADEL) -> Proposal:
    return Proposal.make(
        proposal_id=uuid4(),
        pool=Pool(id=uuid4(), kind=PoolKind.GROUP),
        origin=Origin.PICK,
        poster_id=None,
        sport=sport,
        kind=SearchMode.COMPETITIVE,
        club_id=uuid4(),
        start=START,
        share_grosze=30_00,
        book_by=BOOK_BY,
        at=MADE_AT,
    )


def a_post(poster: UUID = MAREK, sport: Sport = Sport.PADEL) -> Proposal:
    return Proposal.make(
        proposal_id=uuid4(),
        pool=Pool(id=uuid4(), kind=PoolKind.GROUP),
        origin=Origin.POST,
        poster_id=poster,
        sport=sport,
        kind=SearchMode.FOR_FUN,
        club_id=uuid4(),
        start=START,
        share_grosze=27_50,
        book_by=BOOK_BY,
        at=MADE_AT,
    )


def dealt(proposal: Proposal, *versions: tuple[UUID, ...]) -> Proposal:
    for players in versions:
        proposal.deal(players, at=MADE_AT)
    proposal.pull_events()
    return proposal


# --------------------------------------------------------------------------- #
# Born made
# --------------------------------------------------------------------------- #


def test_a_pick_is_born_with_its_court_hour_its_share_and_its_book_by():
    proposal = a_pick()

    [made] = proposal.pull_events()

    assert isinstance(made, ProposalMade)
    assert (made.origin, made.poster_id, made.sport, made.kind) == (
        "PICK",
        None,
        "PADEL",
        "COMPETITIVE",
    )
    assert (made.start, made.share_grosze, made.book_by) == (START, 30_00, BOOK_BY)
    assert proposal.yeses == ()
    assert proposal.seats == 4
    assert proposal.open_seats == 4


def test_posting_is_the_poster_s_yes():
    proposal = a_post()

    made, yes = proposal.pull_events()

    assert isinstance(made, ProposalMade) and made.poster_id == MAREK
    assert yes == YesSaid(
        proposal_id=proposal.proposal_id, player_id=MAREK, occurred_at=MADE_AT
    )
    assert proposal.yeses == (MAREK,)
    assert proposal.open_seats == 3


def test_a_singles_game_has_two_seats():
    assert a_pick(Sport.TENNIS).seats == 2
    assert a_post(sport=Sport.SQUASH).open_seats == 1


def test_a_pick_names_no_poster_and_a_post_needs_one():
    with pytest.raises(InvariantViolated):
        Proposal.make(
            proposal_id=uuid4(),
            pool=Pool(id=uuid4(), kind=PoolKind.GROUP),
            origin=Origin.POST,
            poster_id=None,
            sport=Sport.PADEL,
            kind=SearchMode.COMPETITIVE,
            club_id=uuid4(),
            start=START,
            share_grosze=30_00,
            book_by=BOOK_BY,
            at=MADE_AT,
        )
    with pytest.raises(InvariantViolated):
        Proposal.make(
            proposal_id=uuid4(),
            pool=Pool(id=uuid4(), kind=PoolKind.GROUP),
            origin=Origin.PICK,
            poster_id=MAREK,
            sport=Sport.PADEL,
            kind=SearchMode.COMPETITIVE,
            club_id=uuid4(),
            start=START,
            share_grosze=30_00,
            book_by=BOOK_BY,
            at=MADE_AT,
        )


def test_a_proposal_cannot_be_made_past_its_own_book_by():
    with pytest.raises(InvariantViolated):
        Proposal.make(
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
            at=BOOK_BY,
        )


# --------------------------------------------------------------------------- #
# Versions
# --------------------------------------------------------------------------- #


def test_a_version_names_people_for_the_open_seats():
    proposal = a_post()
    proposal.pull_events()

    proposal.deal((B, C, D), at=LATER)

    [event] = proposal.pull_events()
    assert event == VersionDealt(
        proposal_id=proposal.proposal_id,
        number=1,
        player_ids=(B, C, D),
        occurred_at=LATER,
    )
    assert proposal.version_of(C) is not None
    assert proposal.version_of(C).number == 1


def test_at_most_three_versions_and_each_person_in_one():
    proposal = dealt(a_post(), (B, C, D), (E, F, G), (H,))

    with pytest.raises(InvariantViolated):
        proposal.deal((uuid4(),), at=LATER)
    with pytest.raises(InvariantViolated):
        dealt(a_post(), (B, C, D)).deal((B,), at=LATER)


def test_nobody_already_on_the_game_is_dealt_it_again():
    proposal = a_post()
    with pytest.raises(InvariantViolated):
        proposal.deal((MAREK, B), at=LATER)

    answered = dealt(a_pick(Sport.TENNIS), (B, C))
    answered.say_no(B, at=LATER)
    with pytest.raises(InvariantViolated):
        answered.deal((B,), at=LATER)


def test_a_version_never_names_more_people_than_the_seats_still_open():
    with pytest.raises(InvariantViolated):
        a_post().deal((B, C, D, E), at=LATER)
    with pytest.raises(InvariantViolated):
        a_pick().deal((), at=LATER)
    with pytest.raises(InvariantViolated):
        a_pick().deal((B, B), at=LATER)


def test_a_seat_somebody_said_no_to_is_dealt_again_in_the_same_version():
    """The mechanics §6.2: a no's seat goes to the next best fits — into the
    version it was on, which stays one version."""

    proposal = dealt(a_pick(), (B, C, D, E))
    proposal.say_no(B, at=LATER)

    proposal.deal((F, G), at=LATER, into=1)

    [event] = proposal.pull_events()[-1:]
    assert event == VersionDealt(
        proposal_id=proposal.proposal_id,
        number=1,
        player_ids=(F, G),
        occurred_at=LATER,
    )
    assert len(proposal.versions) == 1
    assert proposal.version_of(F) == proposal.version_of(C)
    assert proposal.version_of(F).players == (B, C, D, E, F, G)


def test_a_seat_is_dealt_to_at_most_three_next_best_fits():
    proposal = dealt(a_post(sport=Sport.TENNIS), (B,))
    proposal.say_no(B, at=LATER)

    with pytest.raises(InvariantViolated):
        proposal.deal((C, D, E, F), at=LATER, into=1)
    with pytest.raises(InvariantViolated):
        proposal.deal((C,), at=LATER, into=2)


# --------------------------------------------------------------------------- #
# Yeses are the game's
# --------------------------------------------------------------------------- #


def test_yeses_on_two_versions_are_in_on_the_one_game():
    """The mechanics §7's own example: Marek posts; B and C say yes on version
    1, E on version 2, and the game is four."""

    proposal = dealt(a_post(), (B, C, D), (E, F, G))

    for player in (B, C, E):
        proposal.say_yes(player, at=LATER)

    assert proposal.yeses == (MAREK, B, C, E)
    assert proposal.open_seats == 0


def test_a_yes_already_said_records_nothing():
    proposal = dealt(a_pick(), (B, C, D, E))
    proposal.say_yes(B, at=LATER)
    proposal.pull_events()

    assert proposal.may_say_yes(B, at=LATER) is False
    proposal.say_yes(B, at=LATER)

    assert proposal.pull_events() == []


def test_somebody_nobody_dealt_it_to_cannot_say_yes():
    proposal = dealt(a_pick(), (B, C, D, E))

    with pytest.raises(ProposalNotFound):
        proposal.say_yes(F, at=LATER)


def test_a_game_with_every_seat_in_takes_no_more_yeses():
    proposal = dealt(a_post(sport=Sport.TENNIS), (B,), (C,))
    proposal.say_yes(B, at=LATER)

    with pytest.raises(ProposalIsFull):
        proposal.say_yes(C, at=LATER)


def test_a_no_is_final_and_a_second_one_records_nothing():
    proposal = dealt(a_pick(), (B, C, D, E))
    proposal.say_no(B, at=LATER)

    [no] = proposal.pull_events()
    assert no == NoSaid(
        proposal_id=proposal.proposal_id, player_id=B, occurred_at=LATER
    )
    proposal.say_no(B, at=LATER)
    assert proposal.pull_events() == []
    with pytest.raises(ProposalAlreadyAnswered):
        proposal.say_yes(B, at=LATER)


def test_somebody_in_says_no_by_withdrawing_rather_than_by_a_no():
    proposal = dealt(a_pick(), (B, C, D, E))
    proposal.say_yes(B, at=LATER)

    with pytest.raises(ProposalAlreadyAnswered):
        proposal.say_no(B, at=LATER)


def test_a_withdrawn_yes_frees_the_seat_and_may_be_said_again():
    """Withdrawing is free (the mechanics §6.5), and unlike a no it is not a
    verdict on the card: while the game fills, the player may be In again."""

    proposal = dealt(a_pick(), (B, C, D, E))
    proposal.say_yes(B, at=LATER)
    proposal.pull_events()

    proposal.withdraw_yes(B, at=LATER)

    assert proposal.pull_events() == [
        YesWithdrawn(proposal_id=proposal.proposal_id, player_id=B, occurred_at=LATER)
    ]
    assert proposal.yeses == ()
    assert proposal.open_seats == 4
    assert proposal.may_say_yes(B, at=LATER) is True
    proposal.say_yes(B, at=LATER)
    assert proposal.yeses == (B,)
    assert proposal.withdrawn == ()


def test_withdrawing_a_yes_never_said_records_nothing():
    proposal = dealt(a_pick(), (B, C, D, E))

    proposal.withdraw_yes(B, at=LATER)

    assert proposal.pull_events() == []
    with pytest.raises(ProposalNotFound):
        proposal.withdraw_yes(F, at=LATER)


def test_a_poster_withdrawing_alone_takes_the_post_with_them():
    proposal = dealt(a_post(), (B, C, D))

    proposal.withdraw_yes(MAREK, at=LATER)

    assert proposal.pull_events() == [
        YesWithdrawn(
            proposal_id=proposal.proposal_id, player_id=MAREK, occurred_at=LATER
        ),
        ProposalWithdrawn(
            proposal_id=proposal.proposal_id, withdrawn_by=MAREK, occurred_at=LATER
        ),
    ]
    assert proposal.standing_at(LATER) is Standing.WITHDRAWN
    with pytest.raises(ProposalIsOver) as over:
        proposal.say_yes(B, at=LATER)
    assert over.value.details == {"standing": "WITHDRAWN"}


def test_a_poster_withdrawing_leaves_the_game_to_those_in():
    proposal = dealt(a_post(), (B, C, D))
    proposal.say_yes(B, at=LATER)
    proposal.pull_events()

    proposal.withdraw_yes(MAREK, at=LATER)

    assert [type(event) for event in proposal.pull_events()] == [YesWithdrawn]
    assert proposal.standing_at(LATER) is Standing.FILLING
    assert proposal.poster_withdrew
    assert proposal.yeses == (B,)


def test_the_last_yes_leaving_a_pick_leaves_it_dealt():
    proposal = dealt(a_pick(), (B, C, D, E))
    proposal.say_yes(B, at=LATER)

    proposal.withdraw_yes(B, at=LATER)

    assert proposal.standing_at(LATER) is Standing.FILLING


# --------------------------------------------------------------------------- #
# The book-by
# --------------------------------------------------------------------------- #


def test_at_its_book_by_a_proposal_has_expired_whether_or_not_anybody_noticed():
    proposal = dealt(a_pick(), (B, C, D, E))

    assert proposal.standing_at(BOOK_BY - timedelta(seconds=1)) is Standing.FILLING
    assert proposal.standing_at(BOOK_BY) is Standing.EXPIRED
    for answer in (proposal.say_yes, proposal.say_no, proposal.withdraw_yes):
        with pytest.raises(ProposalIsOver) as over:
            answer(B, at=BOOK_BY)
        assert over.value.details == {"standing": "EXPIRED"}


def test_the_expiry_is_recorded_once_and_only_once_the_book_by_has_passed():
    proposal = dealt(a_pick(), (B, C, D, E))

    assert proposal.expire(now=BOOK_BY - timedelta(minutes=1)) is False
    assert proposal.expire(now=BOOK_BY) is True
    assert proposal.pull_events() == [
        ProposalExpired(proposal_id=proposal.proposal_id, occurred_at=BOOK_BY)
    ]
    assert proposal.expire(now=BOOK_BY + timedelta(hours=1)) is False
    assert proposal.pull_events() == []


def test_a_withdrawn_post_does_not_expire_as_well():
    proposal = dealt(a_post(), (B, C, D))
    proposal.withdraw_yes(MAREK, at=LATER)
    proposal.pull_events()

    assert proposal.expire(now=BOOK_BY) is False


# --------------------------------------------------------------------------- #
# The court hour
# --------------------------------------------------------------------------- #


def test_a_card_whose_court_hour_went_is_over_and_takes_no_more_answers():
    proposal = dealt(a_pick(), (B, C, D, E))
    proposal.say_yes(B, at=LATER)
    proposal.pull_events()

    assert proposal.lose_court_hour(at=LATER) is True

    assert proposal.pull_events() == [
        CourtHourLost(proposal_id=proposal.proposal_id, occurred_at=LATER)
    ]
    assert proposal.standing_at(LATER) is Standing.COURT_HOUR_LOST
    # Still the record of who was In: they are dealt a new card first.
    assert proposal.yeses == (B,)
    for answer in (proposal.say_yes, proposal.say_no, proposal.withdraw_yes):
        with pytest.raises(ProposalIsOver) as over:
            answer(C, at=LATER)
        assert over.value.details == {"standing": "COURT_HOUR_LOST"}


def test_a_court_hour_is_lost_once_and_never_by_a_card_already_over():
    lost = dealt(a_pick(), (B, C, D, E))
    lost.lose_court_hour(at=LATER)
    lost.pull_events()
    expired = dealt(a_pick(), (B, C, D, E))
    expired.pull_events()

    assert lost.lose_court_hour(at=LATER) is False
    assert lost.expire(now=BOOK_BY) is False
    assert expired.lose_court_hour(at=BOOK_BY) is False
    assert lost.pull_events() == expired.pull_events() == []


# --------------------------------------------------------------------------- #
# The stream
# --------------------------------------------------------------------------- #


def test_the_stream_folds_back_into_the_proposal_it_recorded():
    proposal = a_post()
    proposal.deal((B, C, D), at=LATER)
    proposal.deal((E, F, G), at=LATER)
    proposal.say_yes(E, at=LATER)
    proposal.say_no(C, at=LATER)
    proposal.withdraw_yes(E, at=LATER)
    history = proposal.pull_events()

    folded = Proposal.from_history(history)
    lost = Proposal.from_history(
        [*history, CourtHourLost(proposal_id=proposal.proposal_id, occurred_at=LATER)]
    )

    assert lost.standing_at(LATER) is Standing.COURT_HOUR_LOST

    assert folded.yeses == proposal.yeses == (MAREK,)
    assert folded.versions == proposal.versions
    assert folded.declined == proposal.declined == (C,)
    assert folded.withdrawn == proposal.withdrawn == (E,)
    assert folded.version == len(history)
    assert (folded.start, folded.book_by, folded.share_grosze) == (
        START,
        BOOK_BY,
        27_50,
    )
