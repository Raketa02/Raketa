"""Who may open a record — the three strands, and the partition they run in.

The rule (``docs/adr/0159``): **a record is read through a prior disclosure,
never about a person.** Admitted when the reader *is* the subject, when a search
of theirs returned them, or when the pair share an open challenge or a game — and
never otherwise.

Two properties are asserted here that no route test could see, because both are
about calls that must or must not happen rather than about a status code:

**The gates run in the partition of the disclosure.** A subject rated only in
squash has no index row in a padel partition, so the mutual gender gate cannot be
evaluated there, and *a gate that cannot be evaluated excludes*. Asked in the
partition the disclosure happened in, the row is there and the reader is shown
somebody they demonstrably just saw.

**Nothing is asked before the gate that decides.** The refusal has to happen
before a single provider is touched, or the read would have looked a stranger up
in order to decide it was not allowed to.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.kernel import Instant, Sport, instant
from app.modules.player_record.application.admission import RecordAdmission

NOW: Instant = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))

READER = uuid4()
SUBJECT = uuid4()


class Disclosures:
    """One ``PriorDisclosure``, answering a fixed set of partitions."""

    def __init__(self, *sports: Sport) -> None:
        self.sports = frozenset(sports)
        self.asked: list[tuple[UUID, UUID, Instant]] = []

    async def partitions_between(
        self, *, reader_id: UUID, subject_id: UUID, now: Instant
    ) -> frozenset[Sport]:
        self.asked.append((reader_id, subject_id, now))
        return self.sports


class Gates:
    """A ``RecordGates`` that admits in the partitions it was told to."""

    def __init__(self, *admitting: Sport) -> None:
        self.admitting = frozenset(admitting)
        self.asked: list[Sport] = []

    async def admits(
        self, *, reader_id: UUID, subject_id: UUID, sport: Sport
    ) -> bool:
        self.asked.append(sport)
        return sport in self.admitting


def admission(*, disclosures, gates) -> RecordAdmission:
    return RecordAdmission(disclosures=tuple(disclosures), gates=gates)


async def test_your_own_record_needs_no_disclosure_and_asks_nothing():
    """**The one case with no prior disclosure behind it**, and the one with no
    gates: there is no pair to gate, and a reader is not blocked from
    themselves."""

    searches, gates = Disclosures(Sport.PADEL), Gates(Sport.PADEL)

    admitted = await admission(disclosures=[searches], gates=gates).admits(
        reader_id=READER, subject_id=READER, now=NOW
    )

    assert admitted is True
    assert searches.asked == []
    assert gates.asked == []


async def test_a_stranger_is_refused_before_a_gate_is_evaluated():
    """No disclosure is the ordinary answer about almost everybody, and it costs
    no gate read: there is no partition to evaluate one in."""

    gates = Gates(*Sport)

    admitted = await admission(
        disclosures=[Disclosures(), Disclosures(), Disclosures()], gates=gates
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is False
    assert gates.asked == []


async def test_a_search_that_returned_them_admits_in_that_search_s_sport():
    searches, gates = Disclosures(Sport.PADEL), Gates(Sport.PADEL)

    admitted = await admission(disclosures=[searches], gates=gates).admits(
        reader_id=READER, subject_id=SUBJECT, now=NOW
    )

    assert admitted is True
    assert gates.asked == [Sport.PADEL]
    assert searches.asked == [(READER, SUBJECT, NOW)]


async def test_every_strand_admits_on_its_own():
    """Three sources, one demand. A pair with only a challenge between them and a
    pair with only a game are both admitted, which is what lets the loop's
    surfaces open this sheet without this context learning what they are."""

    for strand in range(3):
        sources = [Disclosures(), Disclosures(), Disclosures()]
        sources[strand] = Disclosures(Sport.TENNIS)

        assert await admission(
            disclosures=sources, gates=Gates(Sport.TENNIS)
        ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)


async def test_the_gate_is_asked_in_the_disclosure_s_partition_and_no_other():
    """**The rule this whole shape exists for.** A subject disclosed in squash is
    gated in squash — the partition where they have an index row — and the padel
    partition is never asked about, because nothing disclosed them there."""

    gates = Gates(Sport.SQUASH)

    admitted = await admission(
        disclosures=[Disclosures(Sport.SQUASH)], gates=gates
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is True
    assert gates.asked == [Sport.SQUASH]


async def test_a_second_disclosure_is_tried_when_the_first_partition_refuses():
    """Each disclosure entitles on its own terms. A pair whose padel row has gone
    from the index are still admitted through the tennis game they played, and
    the alternative — refusing on the first partition that says no — would make
    the answer depend on which strand happened to be read first."""

    gates = Gates(Sport.TENNIS)

    admitted = await admission(
        disclosures=[Disclosures(Sport.PADEL), Disclosures(Sport.TENNIS)],
        gates=gates,
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is True
    assert gates.asked == [Sport.PADEL, Sport.TENNIS]


async def test_the_partitions_are_tried_in_the_registry_s_order():
    """**Never in a set's order** (``docs/adr/0105``). A refusal that depended on
    which partition was asked first would be a record that opens on one process
    and refuses on the next, and the gate reads underneath it are not free."""

    gates = Gates()

    await admission(
        disclosures=[Disclosures(Sport.BADMINTON, Sport.PADEL, Sport.SQUASH)],
        gates=gates,
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert gates.asked == [Sport.PADEL, Sport.SQUASH, Sport.BADMINTON]


async def test_the_gates_stop_at_the_first_partition_that_admits():
    gates = Gates(Sport.PADEL)

    await admission(
        disclosures=[Disclosures(Sport.PADEL, Sport.TENNIS)], gates=gates
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert gates.asked == [Sport.PADEL]


async def test_a_disclosure_the_gates_refuse_everywhere_is_no_entitlement():
    """A block placed since the search still refuses the record. The disclosure
    is what entitles a reader to *ask*; the four gates decide, live, every
    time."""

    admitted = await admission(
        disclosures=[Disclosures(Sport.PADEL, Sport.TENNIS)], gates=Gates()
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is False
