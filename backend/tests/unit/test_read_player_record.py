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
from app.engines.matchfit.core import ReliabilityStrand
from app.modules.player_record.domain.record import (
    GameOutcome,
    LikelyRange,
    OnCourtVerdict,
    OpponentVariety,
    OpinionBand,
    ReliabilityPanel,
    StrandRow,
    SubjectIdentity,
    SubjectRating,
    WhatPlayersSaid,
)

NOW: Instant = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))

READER = uuid4()
SUBJECT = uuid4()
PHOTO = uuid4()


def an_identity(*, photo_id: UUID | None = PHOTO) -> SubjectIdentity:
    return SubjectIdentity(
        name="Karol Tomczyk",
        nickname="karol_t",
        photo_id=photo_id,
        review=OnCourtVerdict.ALLOWED if photo_id else None,
        area_code="A+05151-00013",
        social_tags=("PLAYS_TO_WIN", "HERE_TO_IMPROVE"),
        intro=None,
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


def a_panel(*, pct: int = 90) -> ReliabilityPanel:
    return ReliabilityPanel(
        player_score=pct,
        strands=(
            StrandRow(
                strand=ReliabilityStrand.SHOWS_UP,
                good=9,
                opportunities=10,
                pct=pct,
            ),
        ),
    )


class Reliability:
    def __init__(self, panel: ReliabilityPanel | None = None) -> None:
        self.panel = panel
        self.asked: list[UUID] = []

    async def reliability_of(
        self, player_id: UUID, *, now: Instant
    ) -> ReliabilityPanel | None:
        self.asked.append(player_id)
        return self.panel


class Variety:
    def __init__(self, pair: OpponentVariety | None = None) -> None:
        self.pair = pair
        self.asked: list[UUID] = []

    async def variety_of(
        self, player_id: UUID, *, now: Instant
    ) -> OpponentVariety | None:
        self.asked.append(player_id)
        return self.pair


class Opinions:
    """What other players said, at both resolutions. **It records which was
    asked**, because the whole rule here is which question a sheet is entitled
    to put."""

    def __init__(
        self,
        said: WhatPlayersSaid | None = None,
        band: OpinionBand | None = None,
    ) -> None:
        self.said = said
        self.band = band
        self.asked_for_the_figure: list[UUID] = []
        self.asked_for_the_band: list[UUID] = []

    async def what_players_said(self, player_id: UUID) -> WhatPlayersSaid | None:
        self.asked_for_the_figure.append(player_id)
        return self.said

    async def band_for(self, player_id: UUID) -> OpinionBand | None:
        self.asked_for_the_band.append(player_id)
        return self.band


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
    reliability: Reliability | None = None,
    variety: Variety | None = None,
    sportsmanship: Opinions | None = None,
):
    identities, links = Identities(identity), Links()
    use_case = ReadPlayerRecord(
        admission=Admission(admits),
        identities=identities,
        photos=links,
        ratings=ratings or Ratings(),
        form=form or Form(),
        reliability=reliability or Reliability(),
        variety=variety or Variety(),
        sportsmanship=sportsmanship or Opinions(),
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

    variety = Variety(OpponentVariety(distinct_opponents=9, times_on_court=11))
    reliability = Reliability(a_panel())
    use_case, identities, links = reading(
        admits=False,
        identity=an_identity(),
        reliability=reliability,
        variety=variety,
    )

    with pytest.raises(RecordUnavailable):
        await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert identities.asked == []
    assert links.asked == []
    assert reliability.asked == []
    assert variety.asked == []


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
        reliability=Reliability(),
        variety=Variety(),
        sportsmanship=Opinions(),
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
            reliability=Reliability(),
            variety=Variety(),
            sportsmanship=Opinions(),
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
        reliability=Reliability(),
        variety=Variety(),
        sportsmanship=Opinions(),
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


async def test_the_record_carries_the_pair_and_never_the_share():
    """**Two counts and no percentage.** *Fourteen of twenty* and *seven of ten*
    are the same share and different claims, and the division is a drawing
    decision this context does not make for the client."""

    variety = Variety(OpponentVariety(distinct_opponents=14, times_on_court=20))
    use_case, _, _ = reading(
        admits=True, identity=an_identity(), variety=variety
    )

    record = await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert record.variety == OpponentVariety(distinct_opponents=14, times_on_court=20)
    assert variety.asked == [SUBJECT]


async def test_a_player_no_counted_game_was_watched_for_carries_no_variety():
    """**Absent and never a nought.** A habit nobody has been observed having is
    not a narrow one, and the row is omitted rather than drawn at zero."""

    use_case, _, _ = reading(
        admits=True, identity=an_identity(), variety=Variety(None)
    )

    record = await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert record.variety is None


async def test_a_player_rated_in_nothing_is_still_asked_how_widely_they_play():
    """**Variety is about no sport at all**, so unlike the run of form it is not
    skipped for somebody the sheet resolves no sport for: a newcomer rated in
    nothing may still have played, and the record says so."""

    variety = Variety(OpponentVariety(distinct_opponents=2, times_on_court=3))
    use_case, _, _ = reading(
        admits=True,
        identity=an_identity(),
        ratings=Ratings({}),
        variety=variety,
    )

    record = await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert record.skill is None
    assert record.variety == OpponentVariety(distinct_opponents=2, times_on_court=3)
    assert variety.asked == [SUBJECT]


async def test_the_record_carries_the_pill_and_the_rows_behind_it():
    """**The number the matcher acts on, and what it was the mean of.** Nothing
    here is computed: the panel arrives from the context that owns the
    arithmetic, and the assembler puts it on the sheet."""

    reliability = Reliability(a_panel(pct=90))
    use_case, _, _ = reading(
        admits=True, identity=an_identity(), reliability=reliability
    )

    record = await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert record.reliability == a_panel(pct=90)
    assert reliability.asked == [SUBJECT]


async def test_a_player_nothing_has_fallen_due_for_carries_no_panel():
    """**A third absence, and it is its own.** Somebody rated in four sports who
    has played all year may still have had no plan reach the end of its entry
    window and no seat reach its deadline — and the zone is omitted rather than
    drawn at nought."""

    use_case, _, _ = reading(
        admits=True,
        identity=an_identity(),
        reliability=Reliability(None),
        variety=Variety(OpponentVariety(distinct_opponents=3, times_on_court=4)),
    )

    record = await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert record.reliability is None
    assert record.variety is not None


async def test_a_player_rated_in_nothing_is_still_asked_what_was_watched():
    """Like variety and unlike the run of form, the rows are about no sport —
    so a newcomer the sheet resolves no sport for is still asked."""

    reliability = Reliability(a_panel())
    use_case, _, _ = reading(
        admits=True,
        identity=an_identity(),
        ratings=Ratings({}),
        reliability=reliability,
    )

    record = await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert record.skill is None
    assert record.reliability == a_panel()
    assert reliability.asked == [SUBJECT]


# ---------------------------------------------------------------------------
# What other players said — the one zone that depends on who is reading
# ---------------------------------------------------------------------------


async def test_a_stranger_is_told_the_figure_and_how_many_people_it_rests_on():
    """The count crosses beside the figure, always: `3,0 / 5 · 1 player` is
    visibly one person's opinion and reads as one, which is what lets this
    publish from the very first rating with no minimum."""

    opinions = Opinions(WhatPlayersSaid(average=4.7, raters=17))
    use_case, _, _ = reading(
        admits=True, identity=an_identity(), sportsmanship=opinions
    )

    record = await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert record.sportsmanship == WhatPlayersSaid(average=4.7, raters=17)
    assert record.sportsmanship_band is None
    assert opinions.asked_for_the_figure == [SUBJECT]
    # The band was not asked for and thrown away — it was not asked for.
    assert opinions.asked_for_the_band == []


async def test_the_subject_is_told_a_band_and_the_figure_is_never_asked_for():
    """**The rule this branch exists for** (``docs/adr/0159``, ``docs/adr/0158``).

    A figure and a count on the sheet titled *How others see you* is a
    subtraction: moving from 4,80 over ten to 4,73 over eleven names the new
    rating as a 4, and the subject knows who they played. So the figure is not
    fetched-and-dropped — the question is never put, and there is nothing in this
    process to leak.
    """

    opinions = Opinions(
        WhatPlayersSaid(average=4.7, raters=17), band=OpinionBand.GOOD
    )
    identities, links = Identities(an_identity()), Links()

    record = await ReadOwnRecord(
        identities=identities,
        photos=links,
        ratings=Ratings(),
        form=Form(),
        reliability=Reliability(),
        variety=Variety(),
        sportsmanship=opinions,
        clock=Clock(),
    ).execute(reader_id=READER)

    assert record.sportsmanship_band is OpinionBand.GOOD
    assert record.sportsmanship is None
    assert opinions.asked_for_the_band == [READER]
    assert opinions.asked_for_the_figure == []


async def test_asking_about_yourself_by_id_is_answered_with_the_band_too():
    """The parameterised route reaches the same sheet, so the rule cannot be
    walked around by naming your own id — ``is_self`` decides this and not which
    route was called."""

    opinions = Opinions(
        WhatPlayersSaid(average=2.0, raters=6), band=OpinionBand.POOR
    )
    use_case, _, _ = reading(
        admits=True, identity=an_identity(), sportsmanship=opinions
    )

    record = await use_case.execute(reader_id=READER, subject_id=READER)

    assert record.sportsmanship is None
    assert record.sportsmanship_band is OpinionBand.POOR
    assert opinions.asked_for_the_figure == []


async def test_nobody_has_rated_them_leaves_both_fields_empty():
    """A **fourth absence**, and it asks a fourth question: rating is a favour,
    ignoring the card costs nothing, and nothing anywhere records that somebody
    did not answer. Not a nought, and not a bottom band."""

    use_case, _, _ = reading(admits=True, identity=an_identity())

    record = await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert record.sportsmanship is None
    assert record.sportsmanship_band is None


async def test_a_player_rated_in_nothing_is_still_asked_what_players_said():
    """It is about no sport at all, so a newcomer with no Level still draws this
    zone — the same reason the metered rows and the variety are asked for
    whatever sport resolved."""

    opinions = Opinions(WhatPlayersSaid(average=5.0, raters=2))
    use_case, _, _ = reading(
        admits=True,
        identity=an_identity(),
        ratings=Ratings({}),
        sportsmanship=opinions,
    )

    record = await use_case.execute(reader_id=READER, subject_id=SUBJECT)

    assert record.skill is None
    assert record.sportsmanship == WhatPlayersSaid(average=5.0, raters=2)


def test_a_figure_beside_is_self_is_refused_at_the_record_itself():
    """**The last line of defence, and it is a type's own.** The branch above is
    what decides; this is what makes a branch taken the wrong way loud rather
    than a screen quietly showing somebody the arithmetic of their own
    ratings."""

    from app.kernel import InvariantViolated
    from app.modules.player_record.domain.record import PlayerRecord

    with pytest.raises(InvariantViolated):
        PlayerRecord(
            is_self=True,
            identity=an_identity(),
            photo_url=None,
            sports=(),
            skill=None,
            reliability=None,
            variety=None,
            sportsmanship=WhatPlayersSaid(average=4.7, raters=17),
            sportsmanship_band=None,
        )


def test_a_band_on_a_strangers_record_is_refused_the_same_way():
    """The mirror: the coarse reading exists for the one person the figure is
    withheld from, and drawing it for anybody else would be a second, worse
    answer to a question that already has one."""

    from app.kernel import InvariantViolated
    from app.modules.player_record.domain.record import PlayerRecord

    with pytest.raises(InvariantViolated):
        PlayerRecord(
            is_self=False,
            identity=an_identity(),
            photo_url=None,
            sports=(),
            skill=None,
            reliability=None,
            variety=None,
            sportsmanship=None,
            sportsmanship_band=OpinionBand.GOOD,
        )
