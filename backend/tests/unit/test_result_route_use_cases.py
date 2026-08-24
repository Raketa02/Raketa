"""Reading the result conversation, and joining it: what may be done, and by whom.

Driven through hand-written stubs, so everything below is about the *rules* and
nothing about a database. What the adapters read is
`tests/unit/test_now_adapters.py`'s and `tests/api/test_result.py`'s.

Four claims carry the file:

1. **The three booleans are ADR-0048's permissions, in one place.** Never a
   leaver, never a standby player, accepting is opposing-side only, a side
   proposes once. The two clients hold none of them, so every one is asserted
   here and again on the aggregate that enforces it.
2. **A refusal is not a second shape** (ADR-0070) — and *writes nothing*, which
   is the half a response-shape assertion cannot see.
3. **Two clocks, and the quieter one is present only while it runs.**
4. **The screen and the update are one read at one instant**: the card the update
   carries is the card the strip would have drawn, because both come off
   `card_of`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.kernel import (
    Cover,
    Instant,
    Situation,
    grosze,
    minutes,
    shifted,
)
from app.modules.matches.domain.errors import (
    AcceptanceFromOwnSide,
    MatchNotFound,
    ResultAlreadyAgreed,
    ResultWindowClosed,
    SeatNotTaken,
    SideHasProposed,
)
from app.modules.now.application.result import (
    AcceptCommand,
    AcceptResult,
    ProposeCommand,
    ProposeResult,
    ReadResult,
    ResultQuery,
)
from app.modules.now.domain.enrolled import Enrolment, PlayedScore
from app.modules.now.domain.result import ACCEPTANCE_GRACE_MINUTES
from app.modules.now.domain.screen import CardChanged, Money, Place
from app.modules.now.domain.vocabulary import ActCode

from tests.unit.fake_event_store import CountingUnitOfWork
from tests.unit.match_records import DURATION, a_match, at

WARSAW = ZoneInfo("Europe/Warsaw")
SHARE = grosze(3800)
COURT = grosze(15200)
VIEWER = UUID("11111111-1111-1111-1111-111111111111")
MATCH = UUID("33333333-3333-3333-3333-333333333333")

#: The last point, and the two deadlines measured from it. Spelled out here
#: rather than asked of the kernel: a test that asked the kernel where its
#: boundaries were would agree with it about a deadline that was wrong.
PLAYED = int(DURATION)
ENTRY_DEADLINE = PLAYED + 24 * 60
SETS = ((6, 4), (7, 6))


@dataclass
class _Clock:
    at: datetime

    def now(self) -> datetime:
        return self.at


class StubEnrolled:
    """The membership read, answering whatever a case set up."""

    def __init__(self, row: Enrolment | None) -> None:
        self.row = row
        self.asked = 0

    async def for_player(self, *, player_id: UUID, now: Instant):
        raise AssertionError("the result route never reads the whole strip")

    async def one(
        self, *, player_id: UUID, match_id: UUID, now: Instant
    ) -> Enrolment | None:
        self.asked += 1
        return self.row


class StubResults:
    """The two writes, which either land or raise a refusal."""

    def __init__(self, raises=None) -> None:
        self._raises = raises
        self.proposals: list[tuple[UUID, UUID, tuple[tuple[int, int], ...]]] = []
        self.acceptances: list[tuple[UUID, UUID]] = []

    async def propose(
        self,
        *,
        match_id: UUID,
        player_id: UUID,
        sets: Sequence[tuple[int, int]],
        at: Instant,
    ) -> None:
        self.proposals.append((match_id, player_id, tuple(sets)))
        if self._raises is not None:
            raise self._raises

    async def accept(
        self, *, match_id: UUID, player_id: UUID, at: Instant
    ) -> None:
        self.acceptances.append((match_id, player_id))
        if self._raises is not None:
            raise self._raises


def a_place(**kwargs) -> Place:
    return Place(
        **{
            "club_id": uuid4(),
            "club_name": "Sport Club Krakow",
            "zone": WARSAW,
            "cover": Cover.INDOOR,
            **kwargs,
        }
    )


def played(**facts):
    """A full match that has been played, with whatever result facts a case wants."""

    facts.setdefault("committed_at", at(-2880))
    return a_match(paid=4, **facts)


def a_score(*, viewer_side: int | None = 0, proposed_side: int | None = 0):
    return PlayedScore(
        sides=(("Marta", "Kuba"), ("Ola", "Piotr")),
        sets=SETS,
        viewer_side=viewer_side,
        proposed_side=proposed_side,
    )


def enrolled(record=None, **kwargs) -> Enrolment:
    return Enrolment(
        **{
            "match_id": MATCH,
            "record": record if record is not None else played(),
            "where": a_place(),
            "share": Money(amount=SHARE),
            "court_total": Money(amount=COURT),
            "holds_seat": True,
            **kwargs,
        }
    )


def reading(row: Enrolment | None, *, offset: int):
    enrolled_port = StubEnrolled(row)
    use_case = ReadResult(enrolled=enrolled_port, clock=_Clock(at(offset)))
    return use_case, enrolled_port


async def screen_at(row: Enrolment, *, offset: int):
    use_case, _ = reading(row, offset=offset)
    return await use_case.execute(ResultQuery(player_id=VIEWER, match_id=MATCH))


# --- 1 · who may do what ----------------------------------------------------


async def test_a_bare_table_asks_the_people_who_played_for_a_score():
    screen = await screen_at(enrolled(), offset=PLAYED + 10)

    assert screen.situation.situation is Situation.NEEDS_RESULT
    assert screen.may_enter
    assert not screen.may_accept
    assert not screen.may_counter


async def test_a_leaver_s_screen_opens_and_offers_nothing():
    """ADR-0074's own hardest case. She played half an evening and paid for it;
    a 404 would tell her the match never existed."""

    screen = await screen_at(
        enrolled(holds_seat=False), offset=PLAYED + 10
    )

    assert screen.situation.situation is Situation.NEEDS_RESULT
    assert not screen.may_enter
    assert not screen.may_accept
    assert not screen.may_counter


async def test_a_leaver_looking_at_a_live_proposal_is_still_offered_nothing():
    """The case that separates *she may not* from *there is nothing to answer*.

    She left after the match, so she is still on one side of that net and the
    score reads the right way round for her — and ADR-0048 lets her do none of
    it. Her seat is the whole of what withholds the controls, so a screen
    reading only the score would offer a leaver the accept button.
    """

    row = enrolled(
        holds_seat=False,
        record=played(proposed_at=at(PLAYED + 5), proposals=1),
        score=a_score(viewer_side=0, proposed_side=1),
    )

    screen = await screen_at(row, offset=PLAYED + 10)

    assert screen.situation.situation is Situation.CONFIRM_RESULT
    assert screen.result.score is not None
    assert not screen.may_enter
    assert not screen.may_accept
    assert not screen.may_counter


async def test_a_standby_player_looking_at_a_live_proposal_is_offered_nothing():
    """A standby player never held a seat at all, so the score names neither of
    her sides — and the same one fact withholds the same three controls."""

    row = enrolled(
        holds_seat=False,
        on_standby=True,
        record=played(proposed_at=at(PLAYED + 5), proposals=1),
        score=a_score(viewer_side=None, proposed_side=1),
    )

    screen = await screen_at(row, offset=PLAYED + 10)

    assert not screen.may_enter
    assert not screen.may_accept
    assert not screen.may_counter


async def test_a_standby_player_is_offered_nothing_either():
    screen = await screen_at(
        enrolled(holds_seat=False, on_standby=True), offset=PLAYED + 10
    )

    assert not screen.may_enter
    assert not screen.may_accept
    assert not screen.may_counter


async def test_a_stranger_gets_a_404_and_that_is_the_only_one():
    use_case, _ = reading(None, offset=PLAYED + 10)

    with pytest.raises(MatchNotFound):
        await use_case.execute(ResultQuery(player_id=VIEWER, match_id=MATCH))


async def test_the_other_side_s_score_may_be_accepted_or_countered():
    row = enrolled(
        record=played(proposed_at=at(PLAYED + 5), proposals=1),
        score=a_score(viewer_side=0, proposed_side=1),
    )

    screen = await screen_at(row, offset=PLAYED + 10)

    assert screen.situation.situation is Situation.CONFIRM_RESULT
    assert screen.may_accept
    assert screen.may_counter
    assert not screen.may_enter


async def test_her_own_side_s_score_may_be_corrected_and_never_accepted():
    """*A teammate agreeing with a teammate proves nothing* — and the same rule
    makes her objection credible, which arrives as the freer act."""

    row = enrolled(
        record=played(proposed_at=at(PLAYED + 5), proposals=1),
        score=a_score(viewer_side=0, proposed_side=0),
    )

    screen = await screen_at(row, offset=PLAYED + 10)

    assert screen.may_enter
    assert not screen.may_accept
    assert not screen.may_counter


async def test_once_both_sides_have_spoken_only_an_acceptance_is_left():
    """*A third would be one side repeating itself, and the extra day buys delay
    rather than resolution.*"""

    row = enrolled(
        record=played(proposed_at=at(PLAYED + 20), proposals=2),
        score=a_score(viewer_side=0, proposed_side=1),
    )

    screen = await screen_at(row, offset=PLAYED + 30)

    assert screen.may_accept
    assert not screen.may_counter


async def test_a_settled_result_offers_nothing_and_still_prints_the_score():
    row = enrolled(
        record=played(result_agreed=True),
        score=a_score(viewer_side=0, proposed_side=0),
    )

    screen = await screen_at(row, offset=PLAYED + 60)

    assert screen.situation.situation is Situation.COMPLETED
    assert not (screen.may_enter or screen.may_accept or screen.may_counter)
    assert screen.result.agreed
    assert screen.result.score is not None


async def test_an_unscored_evening_offers_nothing_and_is_not_a_penalty():
    """*Counted and unscored* — never entering a score costs her nothing, and
    there is nowhere on this answer for a penalty to be recorded."""

    screen = await screen_at(enrolled(), offset=ENTRY_DEADLINE + 1)

    assert screen.situation.situation is Situation.PLAYED_NO_SCORE
    assert not (screen.may_enter or screen.may_accept or screen.may_counter)
    assert screen.result.score is None
    assert screen.result.proposals == 0
    assert not hasattr(screen, "penalty")


async def test_a_match_still_forming_resolves_with_an_empty_table():
    """*Dull, correct, and not a special case.*"""

    screen = await screen_at(enrolled(), offset=-2880)

    assert screen.situation.situation is not Situation.NEEDS_RESULT
    assert screen.result.score is None
    assert screen.result.proposals == 0
    assert not screen.may_enter


# --- 2 · the block is four facts, always present ----------------------------


async def test_the_block_is_empty_rather_than_absent_when_nothing_is_up():
    screen = await screen_at(enrolled(), offset=PLAYED + 10)

    assert screen.result is not None
    assert screen.result.score is None
    assert screen.result.proposed_by is None
    assert screen.result.proposals == 0
    assert not screen.result.agreed


async def test_the_viewer_s_side_goes_first_and_the_proposer_is_an_index():
    row = enrolled(
        record=played(proposed_at=at(PLAYED + 5), proposals=1),
        score=a_score(viewer_side=1, proposed_side=1),
    )

    screen = await screen_at(row, offset=PLAYED + 10)

    assert screen.result.score is not None
    assert screen.result.score.sides[0].players == ("Ola", "Piotr")
    # Her side's games first: the stored set is 6-4 to side A, and she is B.
    assert (screen.result.score.sets[0].first, screen.result.score.sets[0].second) == (
        4,
        6,
    )
    # Her own side put it up, so index 0 — her side, wherever it was stored.
    assert screen.result.proposed_by == 0


async def test_the_flip_moves_the_games_with_the_names():
    row = enrolled(
        record=played(proposed_at=at(PLAYED + 5), proposals=1),
        score=a_score(viewer_side=1, proposed_side=0),
    )

    screen = await screen_at(row, offset=PLAYED + 10)

    assert screen.result.score is not None
    assert [(one.first, one.second) for one in screen.result.score.sets] == [
        (4, 6),
        (6, 7),
    ]
    assert screen.result.proposed_by == 1


async def test_no_history_crosses():
    row = enrolled(
        record=played(proposed_at=at(PLAYED + 5), proposals=2),
        score=a_score(viewer_side=0, proposed_side=1),
    )

    screen = await screen_at(row, offset=PLAYED + 10)

    assert screen.result.proposals == 2
    assert not hasattr(screen.result, "history")
    assert not hasattr(screen.result, "previous")


async def test_a_block_cannot_hold_a_score_nobody_proposed() -> None:
    """The two move together, and the type is what says so: *there is a score*
    and *somebody put it there* are one fact, and a block carrying one without
    the other is a screen that draws a scoreline attributed to nobody."""

    from app.modules.now.domain.result import ResultBlock

    with pytest.raises(ValueError):
        ResultBlock(agreed=False, proposals=1, score=None, proposed_by=0)


# --- 3 · two clocks, and the quieter one runs out ---------------------------


async def test_the_hero_clock_is_the_entry_deadline_before_anybody_speaks():
    screen = await screen_at(enrolled(), offset=PLAYED + 10)

    assert screen.settlement_deadline == at(ENTRY_DEADLINE)


async def test_the_hero_clock_becomes_the_proposal_s_own_deadline():
    """Not the match's: a score entered late outlives the entry deadline, and a
    screen counting down to that one would say *over* with the answer running."""

    row = enrolled(
        record=played(proposed_at=at(PLAYED + 120), proposals=1),
        score=a_score(proposed_side=1),
    )

    screen = await screen_at(row, offset=PLAYED + 130)

    assert screen.settlement_deadline == at(PLAYED + 120 + 24 * 60)
    assert screen.settlement_deadline > at(ENTRY_DEADLINE)


async def test_the_grace_is_present_while_it_runs():
    row = enrolled(
        record=played(proposed_at=at(PLAYED + 5), proposals=1),
        score=a_score(proposed_side=1),
    )

    screen = await screen_at(row, offset=PLAYED + 5 + ACCEPTANCE_GRACE_MINUTES - 1)

    assert screen.acceptance_grace == shifted(
        at(PLAYED + 5), minutes(ACCEPTANCE_GRACE_MINUTES)
    )


async def test_the_grace_is_gone_the_moment_it_ends():
    """A moment that has passed is a moment nothing counts to."""

    row = enrolled(
        record=played(proposed_at=at(PLAYED + 5), proposals=1),
        score=a_score(proposed_side=1),
    )

    screen = await screen_at(row, offset=PLAYED + 5 + ACCEPTANCE_GRACE_MINUTES)

    assert screen.acceptance_grace is None
    assert screen.settlement_deadline is not None


async def test_a_bare_table_has_no_grace_at_all():
    screen = await screen_at(enrolled(), offset=PLAYED + 10)

    assert screen.acceptance_grace is None


async def test_both_clocks_are_empty_once_the_answer_is_in():
    row = enrolled(
        record=played(result_agreed=True),
        score=a_score(proposed_side=0),
    )

    screen = await screen_at(row, offset=PLAYED + 60)

    assert screen.settlement_deadline is None
    assert screen.acceptance_grace is None


async def test_an_unscored_evening_counts_to_nothing_rather_than_to_zero():
    screen = await screen_at(enrolled(), offset=ENTRY_DEADLINE + 1)

    assert screen.settlement_deadline is None


# --- 4 · the writes ---------------------------------------------------------


def proposing(row, *, offset: int, raises=None):
    enrolled_port = StubEnrolled(row)
    results = StubResults(raises)
    uow = CountingUnitOfWork()
    use_case = ProposeResult(
        enrolled=enrolled_port,
        results=results,
        uow=uow,
        clock=_Clock(at(offset)),
    )
    return use_case, results, uow


def accepting(row, *, offset: int, raises=None):
    enrolled_port = StubEnrolled(row)
    results = StubResults(raises)
    uow = CountingUnitOfWork()
    use_case = AcceptResult(
        enrolled=enrolled_port,
        results=results,
        uow=uow,
        clock=_Clock(at(offset)),
    )
    return use_case, results, uow


async def test_a_proposal_reaches_the_aggregate_and_commits_once():
    use_case, results, uow = proposing(enrolled(), offset=PLAYED + 10)

    await use_case.execute(
        ProposeCommand(player_id=VIEWER, match_id=MATCH, sets=SETS)
    )

    assert results.proposals == [(MATCH, VIEWER, SETS)]
    assert uow.commits == 1


async def test_an_acceptance_reaches_the_aggregate_and_commits_once():
    row = enrolled(
        record=played(proposed_at=at(PLAYED + 5), proposals=1),
        score=a_score(proposed_side=1),
    )
    use_case, results, uow = accepting(row, offset=PLAYED + 10)

    await use_case.execute(AcceptCommand(player_id=VIEWER, match_id=MATCH))

    assert results.acceptances == [(MATCH, VIEWER)]
    assert uow.commits == 1


async def test_a_write_hands_back_the_screen_and_now_s_update_together():
    use_case, _, _ = proposing(enrolled(), offset=PLAYED + 10)

    answer = await use_case.execute(
        ProposeCommand(player_id=VIEWER, match_id=MATCH, sets=SETS)
    )

    assert isinstance(answer.update, CardChanged)
    assert answer.update.card.match_id == answer.screen.match_id
    assert answer.update.card.situation.situation is answer.screen.situation.situation
    assert answer.update.card.where == answer.screen.where


@pytest.mark.parametrize(
    "refusal",
    [
        SideHasProposed(),
        AcceptanceFromOwnSide(),
        ResultAlreadyAgreed(),
        ResultWindowClosed(),
        SeatNotTaken(),
    ],
    ids=lambda one: type(one).__name__,
)
async def test_every_refusal_answers_with_the_screen_and_commits_nothing(refusal):
    use_case, _, uow = proposing(enrolled(), offset=PLAYED + 10, raises=refusal)

    answer = await use_case.execute(
        ProposeCommand(player_id=VIEWER, match_id=MATCH, sets=SETS)
    )

    assert answer.screen.match_id == MATCH
    assert isinstance(answer.update, CardChanged)
    assert uow.commits == 0


async def test_a_stale_accept_comes_back_as_the_counter_s_situation():
    """ADR-0074's own named case: *"a stale accept comes back as the counter's
    situation with ``mayAccept`` false."* Her tap lost to a counter from her own
    side, so what she gets is the table as it now stands and no way to agree."""

    row = enrolled(
        record=played(proposed_at=at(PLAYED + 20), proposals=2),
        score=a_score(viewer_side=0, proposed_side=0),
    )
    use_case, _, uow = accepting(
        row, offset=PLAYED + 30, raises=AcceptanceFromOwnSide()
    )

    answer = await use_case.execute(AcceptCommand(player_id=VIEWER, match_id=MATCH))

    assert answer.screen.situation.situation is Situation.CONFIRM_RESULT
    assert not answer.screen.may_accept
    assert uow.commits == 0


async def test_a_stranger_writing_never_reaches_the_aggregate():
    use_case, results, uow = proposing(None, offset=PLAYED + 10)

    with pytest.raises(MatchNotFound):
        await use_case.execute(
            ProposeCommand(player_id=VIEWER, match_id=MATCH, sets=SETS)
        )

    assert results.proposals == []
    assert uow.commits == 0


# --- 5 · the card the strip draws -------------------------------------------


async def test_the_card_names_the_act_for_somebody_who_played():
    use_case, _, _ = proposing(enrolled(), offset=PLAYED + 10)

    answer = await use_case.execute(
        ProposeCommand(player_id=VIEWER, match_id=MATCH, sets=SETS)
    )

    assert answer.update.card.act is ActCode.ENTER_RESULT


async def test_the_card_names_no_act_for_a_leaver():
    """The played rung has no membership test, so the situation is the same one
    — and the affordance is what is withheld, which is the split ADR-0030 draws.
    """

    row = enrolled(holds_seat=False)
    use_case, _, _ = proposing(row, offset=PLAYED + 10, raises=SeatNotTaken())

    answer = await use_case.execute(
        ProposeCommand(player_id=VIEWER, match_id=MATCH, sets=SETS)
    )

    assert answer.update.card.situation.situation is Situation.NEEDS_RESULT
    assert answer.update.card.act is None


async def test_a_live_proposal_names_the_answering_act():
    row = enrolled(
        record=played(proposed_at=at(PLAYED + 5), proposals=1),
        score=a_score(proposed_side=1),
    )
    use_case, _, _ = accepting(row, offset=PLAYED + 10)

    answer = await use_case.execute(AcceptCommand(player_id=VIEWER, match_id=MATCH))

    assert answer.update.card.act is ActCode.ANSWER_RESULT
