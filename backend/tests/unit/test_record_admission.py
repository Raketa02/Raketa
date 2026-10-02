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
    """A ``RecordGates`` that admits in the partitions it was told to — and,
    regardless of preference, only when told to."""

    def __init__(self, *admitting: Sport, regardless: bool = False) -> None:
        self.admitting = frozenset(admitting)
        self.regardless = regardless
        self.asked: list[Sport] = []
        self.asked_regardless: list[tuple[UUID, UUID]] = []

    async def admits(
        self, *, reader_id: UUID, subject_id: UUID, sport: Sport
    ) -> bool:
        self.asked.append(sport)
        return sport in self.admitting

    async def admits_regardless_of_preference(
        self, *, reader_id: UUID, subject_id: UUID
    ) -> bool:
        self.asked_regardless.append((reader_id, subject_id))
        return self.regardless


class Runners:
    """A ``RunnerDisclosure`` answering one fixed fact about the pair."""

    def __init__(self, runs: bool = False) -> None:
        self.runs = runs
        self.asked: list[tuple[UUID, UUID]] = []

    async def runs_a_group_of(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        self.asked.append((reader_id, subject_id))
        return self.runs


def admission(*, disclosures, gates, runners: Runners | None = None) -> RecordAdmission:
    return RecordAdmission(
        disclosures=tuple(disclosures),
        runners=runners or Runners(),
        gates=gates,
    )


async def test_your_own_record_needs_no_disclosure_and_asks_nothing():
    """**The one case with no prior disclosure behind it**, and the one with no
    gates: there is no pair to gate, and a reader is not blocked from
    themselves."""

    searches, gates = Disclosures(Sport.PADEL), Gates(Sport.PADEL)
    runners = Runners(True)

    admitted = await admission(
        disclosures=[searches], gates=gates, runners=runners
    ).admits(reader_id=READER, subject_id=READER, now=NOW)

    assert admitted is True
    assert searches.asked == []
    assert runners.asked == []
    assert gates.asked == gates.asked_regardless == []


async def test_a_stranger_is_refused_before_a_gate_is_evaluated():
    """No disclosure is the ordinary answer about almost everybody, and it costs
    no gate read: there is no partition to evaluate one in."""

    gates = Gates(*Sport, regardless=True)

    admitted = await admission(
        disclosures=[Disclosures(), Disclosures(), Disclosures()], gates=gates
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is False
    assert gates.asked == gates.asked_regardless == []


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


# ---------------------------------------------------------------------------
# The fifth strand: whoever runs a group the subject is in
# ---------------------------------------------------------------------------


async def test_whoever_runs_their_group_is_admitted_regardless_of_preference():
    """**The strand that is not a disclosure in sports** (#566). Running a group
    is not being introduced to play with its members, so the gender preference
    is not asked and there is no partition to ask it in — the three gates
    about accounts decide, on the pair, once."""

    runners, gates = Runners(True), Gates(*Sport, regardless=True)

    admitted = await admission(
        disclosures=[Disclosures()], gates=gates, runners=runners
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is True
    assert runners.asked == [(READER, SUBJECT)]
    assert gates.asked == []
    assert gates.asked_regardless == [(READER, SUBJECT)]


async def test_the_gates_about_accounts_still_refuse_whoever_runs_their_group():
    """A block, a hold or an account that may not be shown refuses the
    Administrator as it refuses anybody."""

    admitted = await admission(
        disclosures=[Disclosures()],
        gates=Gates(regardless=False),
        runners=Runners(True),
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is False


async def test_a_disclosure_the_preference_refuses_still_opens_for_whoever_runs_it():
    """An Administrator who plays, and who is in the group they run, is a
    co-member too — and that strand's gates may refuse on a preference. Running
    the group is what admits them then."""

    gates = Gates(regardless=True)

    admitted = await admission(
        disclosures=[Disclosures(Sport.PADEL)], gates=gates, runners=Runners(True)
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is True
    assert gates.asked == [Sport.PADEL]
    assert gates.asked_regardless == [(READER, SUBJECT)]


async def test_who_runs_their_group_is_asked_only_once_the_disclosures_refuse():
    """**The cost is paid on the refusal path and nowhere else.** A record a
    search opened never asks whether the reader runs anything."""

    runners = Runners(True)

    admitted = await admission(
        disclosures=[Disclosures(Sport.PADEL)],
        gates=Gates(Sport.PADEL),
        runners=runners,
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is True
    assert runners.asked == []


async def test_nobody_s_group_run_asks_no_gate_regardless_of_preference():
    gates = Gates(regardless=True)

    admitted = await admission(
        disclosures=[Disclosures()], gates=gates, runners=Runners(False)
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is False
    assert gates.asked_regardless == []
