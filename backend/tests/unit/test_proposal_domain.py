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
    ClubCancelled,
    CourtHourLost,
    NoSaid,
    ProposalExpired,
    ProposalMade,
    ProposalWithdrawn,
    Redealt,
    TurnedDown,
    VersionDealt,
    YesResumed,
    YesSaid,
    YesWithdrawn,
)
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.post import LevelRange, PostedFor, Who
from app.modules.proposals.domain.proposal import (
    ClubAnswer,
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
# Waiting for the club (#543)
# --------------------------------------------------------------------------- #


def a_full_game() -> Proposal:
    proposal = dealt(a_pick(), (B, C, D, E))
    for player in (B, C, D, E):
        proposal.say_yes(player, at=LATER)
    proposal.pull_events()
    return proposal


def test_a_full_game_still_filling_is_waiting_for_its_club():
    proposal = a_full_game()

    assert proposal.waiting_for_the_club is True
    assert dealt(a_pick(), (B, C, D, E)).waiting_for_the_club is False


def test_a_game_waiting_for_its_club_outlives_its_book_by():
    proposal = a_full_game()

    assert proposal.standing_at(BOOK_BY + timedelta(minutes=20)) is Standing.FILLING
    assert proposal.expire(now=BOOK_BY + timedelta(minutes=20)) is False
    assert proposal.pull_events() == []


def test_a_seat_opening_after_its_book_by_leaves_a_game_that_expired():
    proposal = a_full_game()
    late = BOOK_BY + timedelta(minutes=5)

    proposal.withdraw_yes(C, at=late)

    assert proposal.waiting_for_the_club is False
    assert proposal.standing_at(late) is Standing.EXPIRED
    assert proposal.expire(now=late) is True


def test_the_club_turning_it_down_ends_it_and_keeps_who_was_in():
    proposal = a_full_game()

    proposal.turn_down(ClubAnswer.REFUSED, at=LATER)

    assert proposal.pull_events() == [
        TurnedDown(
            proposal_id=proposal.proposal_id, answer="REFUSED", occurred_at=LATER
        )
    ]
    assert proposal.standing_at(LATER) is Standing.TURNED_DOWN
    assert proposal.waiting_for_the_club is False
    assert proposal.yeses == (B, C, D, E)
    with pytest.raises(ProposalIsOver) as over:
        proposal.withdraw_yes(C, at=LATER)
    assert over.value.details == {"standing": "TURNED_DOWN"}


def test_only_a_game_waiting_for_its_club_is_turned_down():
    proposal = dealt(a_pick(), (B, C, D, E))
    proposal.say_yes(B, at=LATER)

    with pytest.raises(InvariantViolated):
        proposal.turn_down(ClubAnswer.NO_ANSWER, at=LATER)


def test_a_turned_down_game_owes_its_people_a_new_card_once():
    proposal = a_full_game()
    proposal.turn_down(ClubAnswer.NO_ANSWER, at=LATER)
    proposal.pull_events()

    assert proposal.owes_a_new_card is True
    assert proposal.redeal(at=LATER) is True
    assert proposal.pull_events() == [
        Redealt(proposal_id=proposal.proposal_id, occurred_at=LATER)
    ]
    assert proposal.owes_a_new_card is False
    assert proposal.redeal(at=LATER) is False
    assert a_full_game().owes_a_new_card is False


def a_booked_game() -> Proposal:
    proposal = a_full_game()
    proposal.fill(first_side=(B, C), second_side=(D, E), at=LATER)
    proposal.pull_events()
    return proposal


def test_a_game_its_club_cancelled_owes_the_people_still_in_a_new_card_once():
    proposal = a_booked_game()

    # E left the booked game before the club cancelled it: only three are owed.
    proposal.club_cancelled((B, C, D), at=LATER)

    assert proposal.pull_events() == [
        ClubCancelled(
            proposal_id=proposal.proposal_id,
            player_ids=(B, C, D),
            occurred_at=LATER,
        )
    ]
    assert proposal.standing_at(LATER) is Standing.FILLED
    assert (proposal.owes_a_new_card, proposal.owed_to) == (True, (B, C, D))
    assert proposal.redeal(at=LATER) is True
    assert proposal.owes_a_new_card is False
    assert a_booked_game().owed_to == (B, C, D, E)


def test_only_a_booked_game_is_cancelled_by_its_club_and_only_once():
    with pytest.raises(InvariantViolated):
        a_full_game().club_cancelled((B, C, D, E), at=LATER)
    proposal = a_booked_game()
    proposal.club_cancelled((B, C, D, E), at=LATER)
    with pytest.raises(InvariantViolated):
        proposal.club_cancelled((B, C, D, E), at=LATER)


# --------------------------------------------------------------------------- #
# The stream
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# A paused week comes back (#544)
# --------------------------------------------------------------------------- #


def test_a_paused_yes_comes_back_as_the_yes_it_was():
    pick = a_pick()
    pick.deal((B, C, D, E), at=MADE_AT)
    pick.say_yes(B, at=MADE_AT)
    pick.pause_yes(B, at=MADE_AT)
    history = pick.pull_events()

    assert pick.resume_yes(B, at=LATER) is True

    assert (pick.yeses, pick.paused) == ((B,), ())
    [event] = pick.pull_events()
    assert isinstance(event, YesResumed)
    assert Proposal.from_history([*history, event]).yeses == (B,)


def test_a_paused_yes_does_not_come_back_to_a_seat_somebody_took():
    pick = dealt(a_pick(Sport.TENNIS), (B, C))
    pick.say_yes(B, at=MADE_AT)
    pick.pause_yes(B, at=MADE_AT)
    pick.say_yes(C, at=MADE_AT)

    assert pick.open_seats == 1
    pick.deal((D,), at=MADE_AT)
    pick.say_yes(D, at=MADE_AT)

    assert pick.resume_yes(B, at=LATER) is False
    assert B in pick.paused


def test_only_a_paused_yes_on_a_game_still_filling_comes_back():
    pick = dealt(a_pick(), (B, C, D, E))
    pick.say_yes(B, at=MADE_AT)

    assert pick.resume_yes(B, at=LATER) is False
    pick.pause_yes(B, at=MADE_AT)
    assert pick.resume_yes(B, at=BOOK_BY) is False


def test_a_block_takes_back_a_paused_yes_and_it_never_comes_back():
    """``docs/adr/0193`` §4: a paused yes is still the blocker's, so a block
    withdraws it — the ordinary ``YesWithdrawn`` — and a freed week finds
    nothing to bring back."""

    pick = a_pick()
    pick.deal((B, C, D, E), at=MADE_AT)
    pick.say_yes(B, at=MADE_AT)
    pick.pause_yes(B, at=MADE_AT)
    history = pick.pull_events()

    assert pick.withdraw_paused_yes(B, at=LATER) is True

    [event] = pick.pull_events()
    assert isinstance(event, YesWithdrawn)
    folded = Proposal.from_history([*history, event])
    assert (folded.yeses, folded.paused, folded.withdrawn) == ((), (), (B,))
    assert folded.resume_yes(B, at=LATER) is False


def test_only_a_paused_yes_on_a_game_still_filling_is_taken_back():
    pick = dealt(a_pick(), (B, C, D, E))
    pick.say_yes(B, at=MADE_AT)

    assert pick.withdraw_paused_yes(B, at=LATER) is False, "a live yes is not paused"
    assert pick.withdraw_paused_yes(C, at=LATER) is False
    pick.pause_yes(B, at=MADE_AT)
    assert pick.withdraw_paused_yes(B, at=BOOK_BY) is False
    assert B in pick.paused


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


# --------------------------------------------------------------------------- #
# Posting a game (#546)
# --------------------------------------------------------------------------- #

WOMEN_AROUND_TWO_SEVENTY_FIVE = PostedFor(
    who=Who.WOMEN, levels=LevelRange(low=2.5, high=3.0)
)


def a_post_for(posted_for: PostedFor) -> Proposal:
    return Proposal.make(
        proposal_id=uuid4(),
        pool=Pool(id=uuid4(), kind=PoolKind.GROUP),
        origin=Origin.POST,
        poster_id=MAREK,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        club_id=uuid4(),
        start=START,
        share_grosze=30_00,
        book_by=BOOK_BY,
        at=MADE_AT,
        posted_for=posted_for,
    )


def test_a_post_records_who_it_is_for_and_its_level_range():
    proposal = a_post_for(WOMEN_AROUND_TWO_SEVENTY_FIVE)

    made, _ = proposal.pull_events()

    assert isinstance(made, ProposalMade)
    assert (made.who, made.level_low, made.level_high) == ("WOMEN", 2.5, 3.0)
    assert proposal.posted_for == WOMEN_AROUND_TWO_SEVENTY_FIVE
    assert Proposal.from_history([made]).posted_for == WOMEN_AROUND_TWO_SEVENTY_FIVE


def test_a_pick_is_for_nobody_in_particular():
    assert a_pick().posted_for is None
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
            at=MADE_AT,
            posted_for=WOMEN_AROUND_TWO_SEVENTY_FIVE,
        )


def test_a_post_made_before_posts_had_a_who_reads_as_for_nobody_in_particular():
    proposal = a_post()
    made, _ = proposal.pull_events()

    assert isinstance(made, ProposalMade)
    assert (made.who, made.level_low, made.level_high) == (None, None, None)
    assert Proposal.from_history([made]).posted_for is None


def test_a_member_never_dealt_a_post_joins_it_with_a_yes():
    proposal = dealt(a_post(), (B, C, D))

    assert proposal.may_join(F, at=LATER) is True
    proposal.join(F, at=LATER)

    assert proposal.pull_events() == [
        YesSaid(proposal_id=proposal.proposal_id, player_id=F, occurred_at=LATER)
    ]
    assert proposal.yeses == (MAREK, F)
    assert proposal.version_of(F) is None


def test_joining_twice_records_nothing():
    proposal = dealt(a_post(), (B, C, D))
    proposal.join(F, at=LATER)
    proposal.pull_events()

    assert proposal.may_join(F, at=LATER) is False
    proposal.join(F, at=LATER)

    assert proposal.pull_events() == []


def test_only_a_post_is_joined_from_outside_its_versions():
    proposal = dealt(a_pick(), (B, C, D, E))

    with pytest.raises(ProposalNotFound):
        proposal.join(F, at=LATER)


def test_a_no_stands_against_joining_and_a_full_or_ended_post_takes_nobody():
    declined = dealt(a_post(), (B, C, D))
    declined.say_no(B, at=LATER)
    full = dealt(a_post(sport=Sport.TENNIS), (B,))
    full.say_yes(B, at=LATER)

    with pytest.raises(ProposalAlreadyAnswered):
        declined.join(B, at=LATER)
    with pytest.raises(ProposalIsFull):
        full.join(F, at=LATER)
    with pytest.raises(ProposalIsOver):
        dealt(a_post(), (B, C, D)).join(F, at=BOOK_BY)
