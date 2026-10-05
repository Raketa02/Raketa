"""The four gates that fail closed, asked directly rather than through a search.

``docs/adr/0095`` reaches **every surface that shows one player to another**, and
the read-back was the second such surface. It is about to have a third, so the
four gates are one collaborator here rather than a private step inside the use
case that happened to need them first — a second spelling of a safety gate is the
defect the whole fail-closed rule exists to prevent.

So the gates are asserted **at their own seam** here rather than only through the
read-back that has them today: the second caller will reach this class and not
that route, and a contract only one surface's tests describe is one the next
surface can quietly bend. Two of these cannot be reached over HTTP at all — the
gates asked about a **sport the reader did not arrive from**, which is the
argument the collaborator takes and the read-back never varies, and the
assertion that the index container is bound **once** whatever the answer turns
out to be.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Collection
from uuid import UUID

import pytest

from app.kernel import Instant, Sport
from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.matchmaking.application.fail_closed_gates import FailClosedGates
from app.modules.matchmaking.domain.candidate_index import CandidateRow, Partition
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.errors import (
    GateDataUnavailable,
    PlayerProfileNotCommitted,
)
from app.modules.player_profile.domain.consent import ConsentSurface
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.player_profile.domain.search_radius import SearchRadius
from app.modules.player_profile.domain.social_tags import SocialTagSelection
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from tests.unit import matchmaking_builders as build

READER = build.SEARCHER_ID
SPORT = build.SPORT


@dataclass
class Profiles:
    profile: PlayerProfile | None

    async def load(self, player_id: UUID) -> PlayerProfile | None:
        return self.profile

    async def save(self, profile: PlayerProfile) -> None:  # pragma: no cover
        raise AssertionError("a gate read never writes a profile")

    async def exists_for(self, *, player_id: UUID) -> bool:  # pragma: no cover
        return self.profile is not None


@dataclass
class Blocks:
    exclusions: frozenset[UUID] = frozenset()
    raises: bool = False

    async def exclusions_for(self, player_id: UUID) -> frozenset[UUID]:
        if self.raises:
            raise BlockStateUnavailable("the block store is unreachable")
        return self.exclusions

    async def blocked_between(self, first: UUID, second: UUID) -> bool:
        return False

    async def blocked_pairs_among(
        self, player_ids: Collection[UUID]
    ) -> frozenset[frozenset[UUID]]:
        """The pairwise mask, which these four gates never ask for.

        Spelled out rather than left off: the stub stands in for the whole
        ``BlockQuery`` protocol, and a stub missing a method is a stub that would
        keep passing on the day the collaborator started calling it.
        """

        return frozenset()


@dataclass
class Holds:
    held: frozenset[UUID] = frozenset()
    raises: bool = False

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        if self.raises:
            raise RuntimeError("the case store is unreachable")
        return frozenset(self.held) & frozenset(player_ids)


@dataclass
class Statuses:
    hidden: frozenset[UUID] = frozenset()

    async def may_not_be_shown(
        self, candidate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        return frozenset(self.hidden) & frozenset(candidate_ids)


@dataclass
class Snapshots:
    """One container per partition, exactly as the real source holds them."""

    rows: tuple[CandidateRow, ...] = ()
    bindings: list[Partition] = field(default_factory=list)

    def snapshot(self, partition: Partition) -> CandidateSnapshot:
        self.bindings.append(partition)
        return CandidateSnapshot(
            partition=partition,
            rows=tuple(row for row in self.rows if row.sport == partition.sport),
            snapshot_version=42,
            caught_up_at=build.NOW,
        )


def a_profile(
    *,
    gender: Gender | None = Gender.WOMAN,
    preference: GenderPreference = GenderPreference.ANY,
    committed_at: datetime = build.SETTLED,
) -> PlayerProfile:
    return PlayerProfile.create(
        player_id=READER,
        social_tags=SocialTagSelection.from_ids(build.TAGS),
        photo_ids=[],
        weekly_hours=WeeklyHours.from_codes(build.SEARCHER_SLOTS),
        location=LocationArea.around(build.CENTRE.latitude, build.CENTRE.longitude),
        search_radius=SearchRadius.chosen(10),
        gender=gender,
        gender_preference=preference,
        proposals_opt_in_accepted=True,
        consent_copy_version="proposals-2026-08",
        consent_surface=ConsentSurface.ONBOARDING,
        idempotency_key="commit-1",
        occurred_at=Instant(committed_at),
    )


def gates(
    *,
    profiles: Profiles | None = None,
    rows: tuple[CandidateRow, ...] | None = None,
    blocks: Blocks | None = None,
    holds: Holds | None = None,
    statuses: Statuses | None = None,
    snapshots: Snapshots | None = None,
) -> FailClosedGates:
    return FailClosedGates(
        profiles=profiles or Profiles(a_profile()),
        candidates=snapshots
        or Snapshots(rows if rows is not None else (build.row(1), build.row(2))),
        blocks=blocks or Blocks(),
        holds=holds or Holds(),
        account_status=statuses or Statuses(),
    )


async def ask(
    collaborator: FailClosedGates, *numbers: int, sport: Sport = SPORT
) -> frozenset[UUID]:
    return await collaborator.withheld_among(
        reader_id=READER,
        subject_ids=tuple(build.player(number) for number in numbers),
        sport=sport,
    )


async def test_a_clear_reader_and_two_indexed_subjects_withholds_nobody():
    assert await ask(gates(), 1, 2) == frozenset()


async def test_a_block_in_either_direction_withholds_that_subject():
    """The set is the reader's own, and it points **both ways** already."""

    withheld = await ask(
        gates(blocks=Blocks(exclusions=frozenset({build.player(2)}))), 1, 2
    )
    assert withheld == frozenset({build.player(2)})


async def test_a_block_against_somebody_not_asked_about_is_not_in_the_answer():
    """The answer is about **these** subjects, and never about the block list.

    The reader's exclusions are their whole list; a caller asking about two
    people gets an answer about two people, so a membership test is the only
    reading of it that exists.
    """

    withheld = await ask(
        gates(blocks=Blocks(exclusions=frozenset({build.player(9)}))), 1, 2
    )
    assert withheld == frozenset()


async def test_a_held_subject_is_withheld():
    withheld = await ask(gates(holds=Holds(held=frozenset({build.player(1)}))), 1, 2)
    assert withheld == frozenset({build.player(1)})


async def test_an_account_that_may_not_be_shown_is_withheld():
    withheld = await ask(
        gates(statuses=Statuses(hidden=frozenset({build.player(1)}))), 1, 2
    )
    assert withheld == frozenset({build.player(1)})


async def test_the_mutual_gender_gate_reads_the_readers_half_live():
    """The reader's preference comes off the profile, never off a stored copy.

    It is the one gate fact its owner can change between being shown somebody and
    asking about them again.
    """

    withheld = await ask(
        gates(
            profiles=Profiles(a_profile(preference=GenderPreference.MEN_ONLY)),
            rows=(build.row(1, gender="WOMAN"), build.row(2, gender="MAN")),
        ),
        1,
        2,
    )
    assert withheld == frozenset({build.player(1)})


async def test_the_other_half_of_the_gender_gate_is_the_index_row():
    withheld = await ask(
        gates(
            rows=(
                build.row(1, gender_preference="MEN_ONLY"),
                build.row(2, gender_preference="ANY"),
            )
        ),
        1,
        2,
    )
    assert withheld == frozenset({build.player(1)})


async def test_a_subject_the_index_does_not_hold_is_withheld():
    """A gate that cannot be evaluated excludes."""

    assert await ask(gates(rows=(build.row(1),)), 1, 2) == frozenset(
        {build.player(2)}
    )


async def test_the_partition_is_the_sport_the_caller_names():
    """**Which partition the row is read from is an argument**, not the reader's.

    A subject rated in squash and asked about in padel has no row in the padel
    container, and *a gate that cannot be evaluated excludes* — which is why the
    caller names the sport the disclosure happened in rather than the sport the
    sheet is about.
    """

    squash_only = gates(rows=(build.row(1, sport=Sport.SQUASH.value),))
    assert await ask(squash_only, 1) == frozenset({build.player(1)})
    assert await ask(squash_only, 1, sport=Sport.SQUASH) == frozenset()


async def test_the_container_is_bound_once_however_many_subjects_are_asked_about():
    snapshots = Snapshots((build.row(1), build.row(2), build.row(3)))
    await ask(gates(snapshots=snapshots), 1, 2, 3)
    assert snapshots.bindings == [Partition.for_sport(SPORT)]


async def test_nobody_to_ask_about_reads_nothing_at_all():
    """An empty question costs no outward read, and the block store proves it."""

    snapshots = Snapshots()
    withheld = await ask(
        gates(blocks=Blocks(raises=True), snapshots=snapshots), sport=SPORT
    )
    assert withheld == frozenset()
    assert snapshots.bindings == []


async def test_an_unreadable_block_set_refuses_rather_than_admitting():
    with pytest.raises(GateDataUnavailable):
        await ask(gates(blocks=Blocks(raises=True)), 1, 2)


async def test_an_unreadable_hold_refuses_rather_than_admitting():
    with pytest.raises(GateDataUnavailable):
        await ask(gates(holds=Holds(raises=True)), 1, 2)


async def test_a_reader_with_no_profile_cannot_have_the_gender_gate_evaluated():
    with pytest.raises(PlayerProfileNotCommitted):
        await ask(gates(profiles=Profiles(None)), 1, 2)


# --------------------------------------------------------------------------- #
# Regardless of preference — for whoever runs a group the subject is in
# --------------------------------------------------------------------------- #


async def ask_regardless(collaborator: FailClosedGates, *numbers: int):
    return await collaborator.withheld_regardless_of_preference(
        reader_id=READER,
        subject_ids=tuple(build.player(number) for number in numbers),
    )


async def test_regardless_of_preference_the_three_about_accounts_still_withhold():
    """A block either way, a hold and an account that may not be shown are
    facts about people rather than about who wants to play with whom, so they
    withhold here exactly as they do beside the preference (#566)."""

    withheld = await ask_regardless(
        gates(
            blocks=Blocks(exclusions=frozenset({build.player(1)})),
            holds=Holds(held=frozenset({build.player(2)})),
            statuses=Statuses(hidden=frozenset({build.player(3)})),
        ),
        1,
        2,
        3,
        4,
    )
    assert withheld == frozenset({build.player(1), build.player(2), build.player(3)})


async def test_regardless_of_preference_reads_no_profile_and_binds_no_container():
    """**The preference is the one gate that is not asked**, so a reader with no
    profile — an Administrator who has never played — is no refusal, and a
    subject whose row would refuse the reader withholds nothing."""

    snapshots = Snapshots((build.row(1, gender_preference="MEN_ONLY"),))

    withheld = await ask_regardless(
        gates(profiles=Profiles(None), snapshots=snapshots), 1, 2
    )

    assert withheld == frozenset()
    assert snapshots.bindings == []


async def test_regardless_of_preference_an_unreadable_block_set_still_refuses():
    with pytest.raises(GateDataUnavailable):
        await ask_regardless(gates(blocks=Blocks(raises=True)), 1)


async def test_regardless_of_preference_nobody_to_ask_about_reads_nothing():
    assert await ask_regardless(gates(blocks=Blocks(raises=True))) == frozenset()
