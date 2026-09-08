"""Every Challenges event survives the round trip through storage, and there are
seven of them.

A durable name is a **published contract**, so three things are asserted: that
each event has one, that an event decoded out of the store equals the event that
was appended, and that **exactly one name announces a conclusion**. The last is
the one that would be quietly widened by a well-meaning addition: a
``challenges.game_on`` would be a second place for a derived standing to be true,
and it is the one a subscriber would believe.

``challenges.withdrawn`` is the exemption and the count of one is the assertion
(``docs/adr/0142`` §3). It is allowed to announce a conclusion because no
arrangement of the seats reaches ``WITHDRAWN``, so the name is the fact's only
home rather than a second one — and that rule is run over the fold itself in
``test_challenge_aggregate.py``.

The round trip is what the seat codes need. A seat is five fields inside one
string precisely because the codec coerces scalars only, and the assertion here
is that a court comes back out of the log as the court that went in — sides,
occupants, answers, per-seat deadlines and origins.
"""

from __future__ import annotations

import pytest

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.modules.challenges.application.event_subscriptions import (
    _CONTRACTS,
    register_challenge_events,
)
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    ChallengeSent,
    ChallengeWithdrawn,
    SeatAccepted,
    SeatDeclined,
    SeatLapsed,
    SeatsInvited,
)
from app.modules.challenges.domain.origins import SentFromSearch, SentOutsideASearch
from app.modules.challenges.domain.seats import Seat, SeatAnswer, Side
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import domain_event_codec, utc

CHALLENGE = new_uuid()
ORGANISER = new_uuid()
ALICE = new_uuid()
SEARCH = new_uuid()
AT = utc(2026, 8, 30)
DEADLINE = utc(2026, 8, 31)

A_COURT = (
    Seat(side=Side.A, player_id=ORGANISER, answer=SeatAnswer.ACCEPTED).code,
    Seat(
        side=Side.A,
        player_id=ALICE,
        answer_by=DEADLINE,
        origin=SentFromSearch(search_id=SEARCH, position=4),
    ).code,
    Seat(side=Side.B).code,
    Seat(
        side=Side.B,
        player_id=new_uuid(),
        answer=SeatAnswer.DECLINED,
        answer_by=DEADLINE,
        origin=SentOutsideASearch(),
    ).code,
)

EVENTS = [
    ChallengeSent(
        challenge_id=CHALLENGE,
        sport="PADEL",
        mode="FOR_FUN",
        window="WEEKEND",
        organiser_id=ORGANISER,
        seats=A_COURT,
        occurred_at=AT,
    ),
    ChallengeOpenedFromMutualInterest(
        challenge_id=CHALLENGE,
        sport="TENNIS",
        organiser_id=ORGANISER,
        other_player_id=ALICE,
        seats=(
            Seat(side=Side.A, player_id=ORGANISER, answer=SeatAnswer.ACCEPTED).code,
            Seat(side=Side.B, player_id=ALICE, answer=SeatAnswer.ACCEPTED).code,
        ),
        occurred_at=AT,
    ),
    SeatAccepted(challenge_id=CHALLENGE, player_id=ALICE, occurred_at=AT),
    SeatDeclined(challenge_id=CHALLENGE, player_id=ALICE, occurred_at=AT),
    SeatLapsed(challenge_id=CHALLENGE, player_id=ALICE, occurred_at=AT),
    SeatsInvited(
        challenge_id=CHALLENGE,
        seats=A_COURT,
        newly_invited=(str(ALICE),),
        occurred_at=AT,
    ),
    ChallengeWithdrawn(challenge_id=CHALLENGE, occurred_at=AT),
]


@pytest.mark.parametrize("event", EVENTS, ids=lambda event: type(event).__name__)
def test_an_event_decodes_back_into_the_event_that_was_appended(event):
    codec = domain_event_codec()

    encoded = codec.encode(event)
    decoded = codec.decode(
        SerializedEventEnvelope(
            id=new_uuid(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=event.occurred_at,
        )
    )

    assert decoded == event


def test_a_court_comes_back_out_of_the_log_as_the_court_that_went_in():
    """The seat code's whole job, asserted on the five fields it carries."""

    codec = domain_event_codec()
    sent = EVENTS[0]

    encoded = codec.encode(sent)
    decoded = codec.decode(
        SerializedEventEnvelope(
            id=new_uuid(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=sent.occurred_at,
        )
    )

    seats = [Seat.from_code(code) for code in decoded.seats]
    assert [seat.side for seat in seats] == [Side.A, Side.A, Side.B, Side.B]
    assert seats[0].answer is SeatAnswer.ACCEPTED and seats[0].answer_by is None
    assert seats[1].answer_by == DEADLINE
    assert seats[1].origin == SentFromSearch(search_id=SEARCH, position=4)
    assert seats[2].player_id is None
    assert seats[3].origin == SentOutsideASearch()


def test_every_event_this_context_records_has_a_durable_name():
    codec = domain_event_codec()

    names = {codec.encode(event).event_type for event in EVENTS}

    assert len(names) == len(EVENTS), "one name per event, none shared"
    assert all(name.startswith("challenges.") for name in names)


def test_there_are_seven_events_and_the_suite_covers_all_of_them():
    """An eighth event added without a round trip here is the failure this catches."""

    registered = {event_cls for event_cls, _ in _CONTRACTS}

    assert len(registered) == 7
    assert {type(event) for event in EVENTS} == registered


def test_one_durable_name_announces_a_conclusion_and_it_is_the_withdrawal():
    """No `GameOn`, no `ChallengeExpired`, no `ChallengeDeclined` — and one
    `challenges.withdrawn`.

    A derived standing has exactly one place to be true, and a published name
    saying otherwise would become the second — and the believed one. The
    withdrawal is the exemption, and it is exempt because there is no *first*
    place: no arrangement of the seats reaches `WITHDRAWN`.

    This is the assertion that goes red the day somebody adds the convenient
    event, and it is written as *exactly one* rather than *none* so that the day
    it goes red is not the day this list quietly grew a second entry.
    """

    catalog = EventCatalog()
    register_challenge_events(catalog)
    names = {name for _, name in _CONTRACTS}

    forbidden = ("game_on", "expired", "declined", "on", "complete", "over")
    conclusions = {name for name in names if name.rsplit(".", 1)[1] in forbidden}
    assert conclusions == set()
    assert {name for name in names if name.rsplit(".", 1)[1] == "withdrawn"} == {
        "challenges.withdrawn"
    }
    # The two that *are* about one seat say so, and neither is the challenge's.
    assert "challenges.seat_declined" in names
    assert "challenges.seat_lapsed" in names
