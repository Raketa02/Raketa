"""Every Challenges event survives the round trip through storage, and there are
nine of them.

A durable name is a **published contract**, so three things are asserted: that
each event has one, that an event decoded out of the store equals the event that
was appended, and that **exactly two names announce a conclusion**. The last is
the one that would be quietly widened by a well-meaning addition: a
``challenges.game_on`` would be a second place for a derived standing to be true,
and it is the one a subscriber would believe.

``challenges.withdrawn`` and ``challenges.called_off`` are the exemptions and the
count of two is the assertion (``docs/adr/0142`` §3, ``docs/adr/0172`` §1). Each
is allowed to announce a conclusion because no arrangement of the seats reaches
``WITHDRAWN`` or ``CALLED_OFF``, so the name is the fact's only home rather
than a second one — and that rule is run over the fold itself in
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
    ChallengeCalledOff,
    ChallengeOpenedFromMutualInterest,
    ChallengeSent,
    ChallengeWithdrawn,
    SeatAccepted,
    SeatDeclined,
    SeatLapsed,
    SeatLeft,
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
        mode="FOR_FUN",
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
    SeatLeft(challenge_id=CHALLENGE, player_id=ALICE, occurred_at=AT),
    SeatsInvited(
        challenge_id=CHALLENGE,
        seats=A_COURT,
        newly_invited=(str(ALICE),),
        occurred_at=AT,
    ),
    ChallengeWithdrawn(challenge_id=CHALLENGE, occurred_at=AT),
    ChallengeCalledOff(challenge_id=CHALLENGE, called_by=ALICE, occurred_at=AT),
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


def test_a_fill_comes_back_naming_who_asked_by_id_and_never_by_text():
    """**The nullable arm, filled.** ``invited_by`` is ``UUID | None``, which is
    not ``UUID``, and a codec that matched the hint by identity handed the
    filled arm back as a string — so the *asked more* line told off this event
    carried its actor as text, equal to no member's id
    ([#408](https://github.com/Raketa02/Raketa/issues/408))."""

    codec = domain_event_codec()
    asked = SeatsInvited(
        challenge_id=CHALLENGE,
        seats=A_COURT,
        newly_invited=(str(ALICE),),
        occurred_at=AT,
        invited_by=ORGANISER,
    )

    encoded = codec.encode(asked)
    decoded = codec.decode(
        SerializedEventEnvelope(
            id=new_uuid(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=encoded.payload,
            occurred_at=asked.occurred_at,
        )
    )

    assert decoded == asked
    assert type(decoded.invited_by) is type(ORGANISER)


def test_a_mutual_minted_before_it_carried_a_mode_still_decodes_as_counted():
    """**The rows already in the store keep decoding** (``.claude/rules/
    domain-events.md``). Every mutual minted before ``docs/adr/0169`` §8 was
    counted, and a row with no ``mode`` key is exactly that: it reads as
    ``None`` rather than being reinterpreted or refused, which is why the
    field is an addition and not a version 2."""

    codec = domain_event_codec()
    mutual = EVENTS[1]
    assert isinstance(mutual, ChallengeOpenedFromMutualInterest)
    encoded = codec.encode(mutual)
    written_before_the_field = {
        key: value for key, value in encoded.payload.items() if key != "mode"
    }

    decoded = codec.decode(
        SerializedEventEnvelope(
            id=new_uuid(),
            event_type=encoded.event_type,
            schema_version=encoded.schema_version,
            payload=written_before_the_field,
            occurred_at=mutual.occurred_at,
        )
    )

    assert isinstance(decoded, ChallengeOpenedFromMutualInterest)
    assert decoded.mode is None
    assert decoded.seats == mutual.seats


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


def test_there_are_nine_events_and_the_suite_covers_all_of_them():
    """A tenth event added without a round trip here is the failure this catches."""

    registered = {event_cls for event_cls, _ in _CONTRACTS}

    assert len(registered) == 9
    assert {type(event) for event in EVENTS} == registered


def test_two_durable_names_announce_a_conclusion_the_withdrawal_and_the_call_off():
    """No `GameOn`, no `ChallengeExpired`, no `ChallengeDeclined` — and
    `challenges.withdrawn` beside `challenges.called_off`.

    A derived standing has exactly one place to be true, and a published name
    saying otherwise would become the second — and the believed one. The two are
    the exemptions, and each is exempt because there is no *first* place: no
    arrangement of the seats reaches `WITHDRAWN` or `CALLED_OFF`
    (``docs/adr/0172`` §1 — the seats reach *deserted* on a game and cannot say
    whether that game is called off).

    This is the assertion that goes red the day somebody adds the convenient
    event, and it is written as *exactly these two* rather than *none* so that
    the day it goes red is not the day this list quietly grew a third entry.
    """

    catalog = EventCatalog()
    register_challenge_events(catalog)
    names = {name for _, name in _CONTRACTS}

    forbidden = ("game_on", "expired", "declined", "on", "complete", "over")
    conclusions = {name for name in names if name.rsplit(".", 1)[1] in forbidden}
    assert conclusions == set()
    assert {
        name
        for name in names
        if name.rsplit(".", 1)[1] in ("withdrawn", "called_off")
    } == {"challenges.withdrawn", "challenges.called_off"}
    # The three that *are* about one seat say so, and none is the challenge's.
    assert "challenges.seat_declined" in names
    assert "challenges.seat_lapsed" in names
    assert "challenges.seat_left" in names
