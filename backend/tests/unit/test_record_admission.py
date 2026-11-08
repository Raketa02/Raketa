"""Who may open a record — the four strands, and the gates after them.

The rule (``docs/adr/0159``): **a record is read through a prior disclosure,
never about a person.** Admitted when the reader *is* the subject, or when the
pair played together, share a group, or the reader runs a group the subject is
in (#575), or the Ranking shows the subject to everybody (``docs/adr/0203`` §9,
#773) — and never otherwise.

Two properties are asserted here that no route test could see, because both are
about calls that must or must not happen rather than about a status code:

**Nothing is asked before the strand that entitles.** A stranger is refused
before a single gate is read, or the read would have looked a stranger up in
order to decide it was not allowed to.

**The first strand that answers yes is enough.** Every strand is admitted under
the same gates, so the gates are asked once, and the strands after it are not
asked at all — the Ranking, asked last, included.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.kernel import Instant, instant
from app.modules.player_record.application.admission import RecordAdmission

READER = uuid4()
SUBJECT = uuid4()
NOW = instant(datetime(2026, 11, 8, 9, tzinfo=timezone.utc))


class Disclosure:
    """One ``PriorDisclosure``, answering one fixed fact about every pair."""

    def __init__(self, discloses: bool = False) -> None:
        self.answer = discloses
        self.asked: list[tuple[UUID, UUID]] = []

    async def discloses(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        self.asked.append((reader_id, subject_id))
        return self.answer


class Everybody:
    """A ``ShownToEverybody`` that shows everybody, or nobody."""

    def __init__(self, shows: bool = False) -> None:
        self.answer = shows
        self.asked: list[tuple[UUID, Instant]] = []

    async def shows(self, subject_id: UUID, *, now: Instant) -> bool:
        self.asked.append((subject_id, now))
        return self.answer


class Gates:
    """A ``RecordGates`` that admits when told to."""

    def __init__(self, admitting: bool = True) -> None:
        self.admitting = admitting
        self.asked: list[tuple[UUID, UUID]] = []

    async def admits(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        self.asked.append((reader_id, subject_id))
        return self.admitting


def admission(*, disclosures, gates, everybody=None) -> RecordAdmission:
    return RecordAdmission(
        disclosures=tuple(disclosures), everybody=everybody or Everybody(), gates=gates
    )


async def test_your_own_record_needs_no_disclosure_and_asks_nothing():
    """**The one case with no prior disclosure behind it**, and the one with no
    gates: there is no pair to gate, and a reader is not blocked from
    themselves."""

    played, everybody, gates = Disclosure(True), Everybody(True), Gates()

    admitted = await admission(
        disclosures=[played], everybody=everybody, gates=gates
    ).admits(reader_id=READER, subject_id=READER, now=NOW)

    assert admitted is True
    assert played.asked == []
    assert everybody.asked == []
    assert gates.asked == []


async def test_a_stranger_is_refused_before_a_gate_is_evaluated():
    """No disclosure is the ordinary answer about almost everybody, and it costs
    no gate read."""

    strands = [Disclosure(), Disclosure(), Disclosure()]
    everybody, gates = Everybody(), Gates()

    admitted = await admission(
        disclosures=strands, everybody=everybody, gates=gates
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is False
    assert gates.asked == []
    assert all(strand.asked == [(READER, SUBJECT)] for strand in strands)
    assert everybody.asked == [(SUBJECT, NOW)]


async def test_every_strand_admits_on_its_own():
    """Three sources, one demand. A pair with only a court between them, only a
    group, or only a group the reader runs are each admitted — which is what
    lets every surface that shows one player to another open this sheet without
    this context learning what it is."""

    for strand in range(3):
        sources = [Disclosure(), Disclosure(), Disclosure()]
        sources[strand] = Disclosure(True)
        gates = Gates()

        assert await admission(disclosures=sources, gates=gates).admits(
            reader_id=READER, subject_id=SUBJECT, now=NOW
        )
        assert gates.asked == [(READER, SUBJECT)]


async def test_the_first_strand_that_answers_yes_ends_the_walk():
    """Every strand is admitted under the same gates, so which one answered
    changes nothing about what is asked next — and the ones after it are not
    asked at all."""

    first, second = Disclosure(True), Disclosure(True)
    everybody, gates = Everybody(True), Gates()

    await admission(
        disclosures=[first, second], everybody=everybody, gates=gates
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert first.asked == [(READER, SUBJECT)]
    assert second.asked == []
    assert everybody.asked == []
    assert gates.asked == [(READER, SUBJECT)]


async def test_the_ranking_admits_a_stranger_through_the_gates():
    """**The fourth strand** (``docs/adr/0203`` §9): nothing between the pair,
    and General lists the subject for everybody — asked at the response's one
    instant, after every disclosure, and still under the gates."""

    strands = [Disclosure(), Disclosure(), Disclosure()]
    everybody, gates = Everybody(True), Gates()

    admitted = await admission(
        disclosures=strands, everybody=everybody, gates=gates
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is True
    assert everybody.asked == [(SUBJECT, NOW)]
    assert gates.asked == [(READER, SUBJECT)]


async def test_a_stranger_the_gates_refuse_is_no_entitlement():
    """A block either way refuses a stranger from the ranking as it refuses a
    group-mate (``docs/adr/0203`` §8)."""

    admitted = await admission(
        disclosures=[], everybody=Everybody(True), gates=Gates(admitting=False)
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is False


async def test_a_disclosure_the_gates_refuse_is_no_entitlement():
    """A block placed since the game still refuses the record. The disclosure
    is what entitles a reader to *ask*; the gates decide, live, every time."""

    admitted = await admission(
        disclosures=[Disclosure(True)], gates=Gates(admitting=False)
    ).admits(reader_id=READER, subject_id=SUBJECT, now=NOW)

    assert admitted is False
