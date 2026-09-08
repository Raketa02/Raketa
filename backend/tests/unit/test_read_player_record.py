"""Reading one record: the order of the reads, and what an absence costs.

Two use cases over one assembler, and the split is the wiring rather than a
duplication: ``ReadOwnRecord`` has **no admission collaborator at all**, so the
route for your own sheet cannot be taken down by the machinery that gates
somebody else's — and *the self case has no gates* is a fact about the dependency
graph instead of a branch somebody could delete.

The order asserted here is the one thing a route test cannot see: **a refused
read touches no provider.** A read that fetched a stranger's handle and
photograph and *then* decided it was not allowed to would have done the lookup
the whole admission rule exists to prevent.

Two more things the assembler owns are asserted here rather than over HTTP: the
sport asked for reaches the **sheet's contents and never its admission**, and a
player rated in nothing is never asked for a run of form — because there is no
sport to ask one about, and asking and discarding is the difference between a
newcomer's record being cheap and it costing what anybody's does.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from app.kernel import Instant, Sport, instant
from app.modules.player_record.application.read_player_record import (
    ReadOwnRecord,
    ReadPlayerRecord,
)
from app.modules.player_record.domain.errors import RecordUnavailable
from app.modules.player_record.domain.record import (
    GameOutcome,
    LikelyRange,
    OnCourtVerdict,
    SubjectIdentity,
    SubjectRating,
)

NOW: Instant = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))

READER = uuid4()
SUBJECT = uuid4()
PHOTO = uuid4()


def an_identity(*, photo_id: UUID | None = PHOTO) -> SubjectIdentity:
    return SubjectIdentity(
        nickname="Karol T.",
        photo_id=photo_id,
        review=OnCourtVerdict.ALLOWED if photo_id else None,
        area_code="A+05151-00013",
        social_tags=("PLAYS_TO_WIN", "HERE_TO_IMPROVE"),
    )


class Identities:
    def __init__(self, identity: SubjectIdentity | None = None) -> None:
        self.identity = identity
        self.asked: list[UUID] = []

    async def identity_of(self, player_id: UUID) -> SubjectIdentity | None:
        self.asked.append(player_id)
        return self.identity


class Links:
    def __init__(self) -> None:
        self.asked: list[tuple[UUID, UUID]] = []

    async def link_for(self, *, owner_id: UUID, photo_id: UUID) -> str:
        self.asked.append((owner_id, photo_id))
        return f"https://photos.example/{owner_id}/{photo_id}?signed"


def a_rating(sport: Sport, *, counted: int = 4) -> SubjectRating:
    return SubjectRating(
        sport=sport,
        level=3.2,
        band="Established",
        confidence=71,
        counted_games=counted,
        likely_range=LikelyRange(low=2.9, high=3.5),
    )


class Ratings:
    def __init__(self, held: dict[Sport, SubjectRating] | None = None) -> None:
        self.held = held if held is not None else {Sport.PADEL: a_rating(Sport.PADEL)}
        self.asked: list[UUID] = []

    async def ratings_of(self, player_id: UUID) -> dict[Sport, SubjectRating]:
        self.asked.append(player_id)
        return self.held


class Form:
    def __init__(self, run: tuple[GameOutcome, ...] = ()) -> None:
        self.run = run
        self.asked: list[tuple[UUID, Sport]] = []

    async def last_results_in(
        self, player_id: UUID, *, sport: Sport, now: Instant
    ) -> tuple[GameOutcome, ...]:
        self.asked.append((player_id, sport))
        return self.run


class Admission:
    def __init__(self, verdict: bool) -> None:
        self.verdict = verdict
        self.asked: list[tuple[UUID, UUID]] = []

    async def admits(
        self, *, reader_id: UUID, subject_id: UUID, now: Instant
    ) -> bool:
        self.asked.append((reader_id, subject_id))
        return self.verdict


class Clock:
    def now(self) -> Instant:
        return NOW


def reading(
    *,
    admits: bool,
    identity: SubjectIdentity | None,
    ratings: Ratings | None = None,
    form: Form | None = None,
):
    identities, links = Identities(identity), Links()
    use_case = ReadPlayerRecord(
        admission=Admission(admits),
        identities=identities,
        photos=links,
        ratings=ratings or Ratings(),
        form=form or Form(),
        clock=Clock(),
    )
    return use_case, identities, links


async def test_a_record_carries_the_identity_and_a_link_minted_for_it():
    use_case, identities, links = reading(admits=True, identity=an_identity())

    record = await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert record.is_self is False
    assert record.identity == an_identity()
    assert record.photo_url == f"https://photos.example/{SUBJECT}/{PHOTO}?signed"
    assert identities.asked == [SUBJECT]
    # Signed as the person on the record, never as the person looking: the store
    # keys the pair, so a link signed under the reader's id reaches nothing.
    assert links.asked == [(SUBJECT, PHOTO)]


async def test_a_player_with_no_photograph_has_no_address_to_sign():
    """Not an empty string and not a link to nothing: the field is absent and the
    client draws the generated court poster."""

    use_case, _, links = reading(admits=True, identity=an_identity(photo_id=None))

    record = await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert record.photo_url is None
    assert links.asked == []


async def test_a_refused_read_touches_no_provider():
    """**The order, and the whole reason it is asserted.** A read that looked a
    stranger up and then refused would have done the lookup the admission rule
    exists to prevent."""

    use_case, identities, links = reading(admits=False, identity=an_identity())

    with pytest.raises(RecordUnavailable):
        await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert identities.asked == []
    assert links.asked == []


async def test_a_person_the_platform_cannot_describe_refuses_the_same_way():
    """*No such player* is the fourth cause of the one refusal. It reaches the
    same class, so it renders as the same body as a block does."""

    use_case, _, _ = reading(admits=True, identity=None)

    with pytest.raises(RecordUnavailable):
        await use_case.execute(reader_id=READER, subject_id=SUBJECT)


async def test_your_own_id_on_the_parameterised_route_still_reads_as_your_own():
    """``is_self`` is the server's answer wherever the read came from — the route
    for a given player, asked about yourself, is your own record."""

    use_case, _, _ = reading(admits=True, identity=an_identity())

    record = await use_case.execute(reader_id=READER, subject_id=READER)

    assert record.is_self is True


async def test_your_own_record_is_read_with_no_admission_collaborator_at_all():
    """The ``/me`` route has no gates to be short-circuited: there is nothing
    wired in to short-circuit."""

    identities, links = Identities(an_identity()), Links()

    record = await ReadOwnRecord(
        identities=identities,
        photos=links,
        ratings=Ratings(),
        form=Form(),
        clock=Clock(),
    ).execute(reader_id=READER)

    assert record.is_self is True
    assert record.identity == an_identity()
    assert identities.asked == [READER]


async def test_a_reader_whose_own_identity_cannot_be_read_is_refused_alike():
    identities = Identities(None)

    with pytest.raises(RecordUnavailable):
        await ReadOwnRecord(
            identities=identities,
            photos=Links(),
            ratings=Ratings(),
            form=Form(),
            clock=Clock(),
        ).execute(reader_id=READER)


async def test_the_sport_asked_for_reaches_the_sheet_and_never_the_admission():
    """**Two questions, and a client may only influence one of them.** What the
    sheet is about is the reader's arrival context; who may be seen is decided in
    the partitions the platform already showed them in."""

    admission = Admission(True)
    form = Form()
    use_case = ReadPlayerRecord(
        admission=admission,
        identities=Identities(an_identity()),
        photos=Links(),
        ratings=Ratings({Sport.SQUASH: a_rating(Sport.SQUASH)}),
        form=form,
        clock=Clock(),
    )

    record = await use_case.execute(
        reader_id=READER, subject_id=SUBJECT, arrived_from=Sport.TENNIS
    )

    # The admission was asked about the pair and about nothing else — there is
    # nowhere on it for a sport a client sent to arrive.
    assert admission.asked == [(READER, SUBJECT)]
    # And the sheet fell back rather than being refused for a sport they do not
    # play.
    assert record.skill is not None and record.skill.sport is Sport.SQUASH
    assert form.asked == [(SUBJECT, Sport.SQUASH)]


async def test_the_run_of_form_is_asked_for_in_the_resolved_sport():
    form = Form(run=(GameOutcome.WIN, GameOutcome.LOSS))
    use_case, _, _ = reading(
        admits=True,
        identity=an_identity(),
        ratings=Ratings(
            {
                Sport.PADEL: a_rating(Sport.PADEL, counted=1),
                Sport.SQUASH: a_rating(Sport.SQUASH, counted=9),
            }
        ),
        form=form,
    )

    record = await use_case.execute(
        reader_id=READER, subject_id=SUBJECT, arrived_from=Sport.PADEL
    )

    assert record.skill is not None
    assert record.skill.sport is Sport.PADEL
    assert record.skill.last_five == (GameOutcome.WIN, GameOutcome.LOSS)
    assert form.asked == [(SUBJECT, Sport.PADEL)]


async def test_a_player_rated_in_nothing_is_asked_for_no_run_at_all():
    """**Not asked and discarded — not asked.** There is no sport to ask about,
    and a newcomer's record costs a fold nobody would read."""

    form = Form()
    use_case, _, _ = reading(
        admits=True, identity=an_identity(), ratings=Ratings({}), form=form
    )

    record = await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert record.skill is None
    assert record.sports == ()
    assert form.asked == []


async def test_the_pills_carry_every_rated_sport_and_the_panel_carries_one():
    use_case, _, _ = reading(
        admits=True,
        identity=an_identity(),
        ratings=Ratings(
            {
                Sport.PADEL: a_rating(Sport.PADEL),
                Sport.BADMINTON: a_rating(Sport.BADMINTON),
            }
        ),
    )

    record = await use_case.execute(
        reader_id=READER, subject_id=SUBJECT, arrived_from=Sport.BADMINTON
    )

    assert [one.sport for one in record.sports] == [Sport.PADEL, Sport.BADMINTON]
    assert record.skill is not None and record.skill.sport is Sport.BADMINTON
