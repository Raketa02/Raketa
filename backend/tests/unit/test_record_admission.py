"""Who may open a record — rule (b), then the gates (``docs/adr/0204`` §2).

**A record opens for any reader**, unless a block stands between the two
(a gate) or the subject turned *Show me to new people* off and the reader
shares no group, no game and no friendship with them, nor runs a group they
are in (``WithinReach``).

Three properties are asserted here that no route test could see, because each
is about calls that must or must not happen rather than about a status code:

**The switch is asked first, and a subject with it on costs no strand.** For
almost everybody the answer is one profile read.

**Nothing is asked of the gates before rule (b) admits**, so a switched-off
stranger is refused without a gate being read.

**The first strand that answers yes is enough**, and the ones after it are not
asked at all.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from app.modules.player_record.application.admission import (
    RecordAdmission,
    WithinReach,
)

READER = uuid4()
SUBJECT = uuid4()


class Disclosure:
    """One ``PriorDisclosure``, answering one fixed fact about every pair."""

    def __init__(self, discloses: bool = False) -> None:
        self.answer = discloses
        self.asked: list[tuple[UUID, UUID]] = []

    async def discloses(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        self.asked.append((reader_id, subject_id))
        return self.answer


class Switch:
    """An ``OpenToNewPeople`` with the switch on, or off."""

    def __init__(self, on: bool = True) -> None:
        self.on = on
        self.asked: list[UUID] = []

    async def open_to_new_people(self, subject_id: UUID) -> bool:
        self.asked.append(subject_id)
        return self.on


class Gates:
    """A ``RecordGates`` that admits when told to."""

    def __init__(self, admitting: bool = True) -> None:
        self.admitting = admitting
        self.asked: list[tuple[UUID, UUID]] = []

    async def admits(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        self.asked.append((reader_id, subject_id))
        return self.admitting


def admission(*, switch, disclosures=(), gates=None) -> RecordAdmission:
    return RecordAdmission(
        reach=WithinReach(new_people=switch, disclosures=tuple(disclosures)),
        gates=gates or Gates(),
    )


async def test_your_own_record_asks_nothing():
    """The one case with no gates: there is no pair to gate, and a switch
    turned off closes nobody's own record."""

    switch, strand, gates = Switch(on=False), Disclosure(), Gates()

    admitted = await admission(switch=switch, disclosures=[strand], gates=gates).admits(
        reader_id=READER, subject_id=READER
    )

    assert admitted is True
    assert (switch.asked, strand.asked, gates.asked) == ([], [], [])


async def test_a_stranger_opens_a_record_with_the_switch_on_and_no_strand_is_asked():
    """**Any reader**: nothing between the pair, and the record opens — under
    the gates, and without a strand read."""

    switch, strands, gates = Switch(on=True), [Disclosure(), Disclosure()], Gates()

    admitted = await admission(switch=switch, disclosures=strands, gates=gates).admits(
        reader_id=READER, subject_id=SUBJECT
    )

    assert admitted is True
    assert switch.asked == [SUBJECT]
    assert all(strand.asked == [] for strand in strands)
    assert gates.asked == [(READER, SUBJECT)]


async def test_a_switched_off_stranger_is_refused_before_a_gate_is_read():
    switch, strands, gates = Switch(on=False), [Disclosure() for _ in range(4)], Gates()

    admitted = await admission(switch=switch, disclosures=strands, gates=gates).admits(
        reader_id=READER, subject_id=SUBJECT
    )

    assert admitted is False
    assert all(strand.asked == [(READER, SUBJECT)] for strand in strands)
    assert gates.asked == []


async def test_each_strand_admits_a_switched_off_subject_on_its_own():
    """A group shared, a friendship, a request they sent the reader, a court
    shared, a group the reader runs: any one of them keeps the record open."""

    for strand in range(5):
        sources = [Disclosure() for _ in range(5)]
        sources[strand] = Disclosure(True)
        gates = Gates()

        assert await admission(
            switch=Switch(on=False), disclosures=sources, gates=gates
        ).admits(reader_id=READER, subject_id=SUBJECT)
        assert gates.asked == [(READER, SUBJECT)]


async def test_the_first_strand_that_answers_yes_ends_the_walk():
    first, second = Disclosure(True), Disclosure(True)

    await admission(switch=Switch(on=False), disclosures=[first, second]).admits(
        reader_id=READER, subject_id=SUBJECT
    )

    assert first.asked == [(READER, SUBJECT)]
    assert second.asked == []


async def test_the_gates_refuse_whatever_rule_b_admitted():
    """A block either way refuses a stranger with the switch on as it refuses a
    group-mate (``docs/adr/0203`` §8)."""

    on = admission(switch=Switch(on=True), gates=Gates(admitting=False))
    mate = admission(
        switch=Switch(on=False),
        disclosures=[Disclosure(True)],
        gates=Gates(admitting=False),
    )

    assert await on.admits(reader_id=READER, subject_id=SUBJECT) is False
    assert await mate.admits(reader_id=READER, subject_id=SUBJECT) is False


async def test_rule_b_alone_is_what_a_friend_request_asks():
    """``WithinReach`` is the record's rule (b) and nothing else — no gate, no
    self — so Friends can ask it of a request without a block deciding it."""

    reach = WithinReach(new_people=Switch(on=False), disclosures=[Disclosure()])
    open_reach = WithinReach(new_people=Switch(on=True), disclosures=[])

    assert await reach.reaches(reader_id=READER, subject_id=SUBJECT) is False
    assert await open_reach.reaches(reader_id=READER, subject_id=SUBJECT) is True
