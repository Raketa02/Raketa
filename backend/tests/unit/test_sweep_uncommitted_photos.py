"""The sweep: an orphan past the window goes, a referenced photo never does.

**The two directions are the whole test, and they are not symmetric.** Failing
to delete an orphan costs storage. Deleting a referenced photo destroys
something a player put in their profile and cannot get back — so the referenced
cases here are deliberately hostile: far past the window, mixed in the same
listing as orphans of the same owner, and re-checked on a second run.

The **event store is faked, not the repository**, for the reason the commit's
tests fake it: the sweep asks whether a *committed profile* names a photo, and
that answer comes out of a replay. A faked repository would answer from a
dictionary somebody wrote by hand, and the question would stop being the one
production asks.

Ageing a photo is moving the fake store's `now` before storing it. No test here
sleeps, and no test here needs MinIO.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import pytest

from app.kernel import Instant, instant
from app.modules.player_profile.application.sweep_uncommitted_photos import (
    SweepUncommittedPhotos,
)
from app.modules.player_profile.domain.consent import ConsentSurface
from app.modules.player_profile.domain.availability import AvailabilityGrid
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.photos import (
    UNCOMMITTED_PHOTO_RETENTION_HOURS,
    PhotoRef,
    TranscodedImage,
)
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.player_profile.domain.search_radius import SearchRadius
from app.modules.player_profile.domain.social_tags import SocialTagSelection
from app.modules.player_profile.infrastructure.event_sourced_player_profile_repository import (  # noqa: E501
    EventSourcedPlayerProfileRepository,
)
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import InMemoryEventStore, RecordingPublisher
from tests.unit.fake_photo_storage import DEFAULT_NOW, InMemoryPhotoStorage

#: Two owners, written out rather than generated, so a listing's order is
#: something a failure message can be read against.
ALICE = UUID("11111111-1111-1111-1111-111111111111")
BOB = UUID("22222222-2222-2222-2222-222222222222")

#: The instant every test sweeps at. The store's default `now`, so "just
#: uploaded" needs no arrangement and ageing is subtraction.
NOW: Instant = DEFAULT_NOW

IMAGE = TranscodedImage(data=b"jpeg", media_type="image/jpeg", width=10, height=10)


def ago(hours: float) -> Instant:
    return instant(NOW - timedelta(hours=hours))


class SweepClock:
    """A clock the test moves, so the window is measured and not assumed."""

    def __init__(self, at: Instant = NOW) -> None:
        self.at = at

    def now(self) -> Instant:
        return self.at


class CountingProfiles:
    """The real repository, counting the players it was asked to replay.

    Wrapped rather than reimplemented: the sweep's cost is one replay per
    *owner* rather than per photo, and that is a property of the use case which
    is invisible in the objects it deletes.
    """

    def __init__(self, inner: EventSourcedPlayerProfileRepository) -> None:
        self._inner = inner
        self.loaded: list[UUID] = []

    async def load(self, player_id: UUID) -> PlayerProfile | None:
        self.loaded.append(player_id)
        return await self._inner.load(player_id)

    async def save(self, profile: PlayerProfile) -> None:
        await self._inner.save(profile)

    async def exists_for(self, *, player_id: UUID) -> bool:
        return await self._inner.exists_for(player_id=player_id)


class Harness:
    def __init__(self) -> None:
        self.store = InMemoryEventStore()
        self.publisher = RecordingPublisher()
        self.photos = InMemoryPhotoStorage()
        self.clock = SweepClock()
        self.profiles = CountingProfiles(
            EventSourcedPlayerProfileRepository(
                event_store=self.store, events=self.publisher
            )
        )

    def sweep(self) -> SweepUncommittedPhotos:
        return SweepUncommittedPhotos(
            storage=self.photos, profiles=self.profiles, clock=self.clock
        )

    async def upload(self, owner_id: UUID, *, hours_ago: float = 0.0) -> PhotoRef:
        """A photo the store took `hours_ago`, the way an upload leaves one."""

        ref = PhotoRef(owner_id=owner_id, photo_id=new_uuid())
        self.photos.now = ago(hours_ago)
        await self.photos.put(ref, IMAGE, metadata={})
        return ref

    async def commit_profile(self, owner_id: UUID, *refs: PhotoRef) -> None:
        """A committed profile naming exactly these photos, in this order."""

        profile = PlayerProfile.create(
            player_id=owner_id,
            social_tags=SocialTagSelection.from_ids(
                ("PLAYS_TO_WIN", "HERE_TO_IMPROVE")
            ),
            photo_ids=[ref.photo_id for ref in refs],
            availability=AvailabilityGrid.of_cells(()),
            location=LocationArea.around(52.23, 21.01),
            search_radius=SearchRadius.chosen(10),
            proposals_opt_in_accepted=True,
            consent_copy_version="v1",
            consent_surface=ConsentSurface.ONBOARDING,
            idempotency_key=str(new_uuid()),
            occurred_at=instant(NOW),
        )
        await self.profiles.save(profile)


# ---------------------------------------------------------------------------
# The two directions the acceptance criteria name
# ---------------------------------------------------------------------------


async def test_an_orphan_past_the_window_is_deleted():
    """Uploaded, never committed, a day old: paid-for storage attached to no
    account state, which is the whole reason this job exists."""

    harness = Harness()
    orphan = await harness.upload(
        ALICE, hours_ago=UNCOMMITTED_PHOTO_RETENTION_HOURS + 1
    )

    report = await harness.sweep().execute()

    assert orphan not in harness.photos.objects
    assert harness.photos.deletions == [orphan]
    assert (report.examined, report.deleted) == (1, 1)


async def test_a_photo_a_profile_references_is_never_swept():
    """Regardless of age — a profile photo is a year old on its first birthday
    and is not an orphan on any of them."""

    harness = Harness()
    kept = await harness.upload(ALICE, hours_ago=24 * 365)
    await harness.commit_profile(ALICE, kept)

    report = await harness.sweep().execute()

    assert kept in harness.photos.objects
    assert harness.photos.deletions == []
    assert (report.examined, report.deleted) == (1, 0)


async def test_a_photo_inside_the_window_is_left_alone():
    """The social part takes minutes. A photo uploaded an hour ago belongs to a
    commit that may still be about to happen."""

    harness = Harness()
    fresh = await harness.upload(ALICE, hours_ago=1)

    report = await harness.sweep().execute()

    assert fresh in harness.photos.objects
    assert (report.examined, report.deleted) == (0, 0)


async def test_the_window_is_measured_from_the_clock_not_from_startup():
    """The same photo, swept twice at two different nows.

    Fixes the window as a *rule* rather than as whatever the store happened to
    return: nothing about the photo changes between these two runs, only the
    time it is asked at.
    """

    harness = Harness()
    photo = await harness.upload(ALICE, hours_ago=1)

    await harness.sweep().execute()
    assert photo in harness.photos.objects

    harness.clock.at = instant(NOW + timedelta(hours=UNCOMMITTED_PHOTO_RETENTION_HOURS))
    await harness.sweep().execute()

    assert photo not in harness.photos.objects


# ---------------------------------------------------------------------------
# The mixed cases, which are where a wrong answer destroys something
# ---------------------------------------------------------------------------


async def test_one_owner_keeps_what_they_committed_and_loses_what_they_did_not():
    """The real shape of onboarding: four tiles filled, three committed.

    Both kinds sit in one listing under one owner, so a sweep that decided per
    *owner* rather than per *photo* fails here in one direction or the other.
    """

    harness = Harness()
    old = UNCOMMITTED_PHOTO_RETENTION_HOURS + 2
    committed = [await harness.upload(ALICE, hours_ago=old) for _ in range(3)]
    abandoned = await harness.upload(ALICE, hours_ago=old)
    await harness.commit_profile(ALICE, *committed)

    report = await harness.sweep().execute()

    assert set(harness.photos.objects) == set(committed)
    assert harness.photos.deletions == [abandoned]
    assert (report.examined, report.deleted) == (4, 1)


async def test_one_players_orphans_do_not_reach_another_players_photos():
    harness = Harness()
    old = UNCOMMITTED_PHOTO_RETENTION_HOURS + 2
    bobs = await harness.upload(BOB, hours_ago=old)
    await harness.commit_profile(BOB, bobs)
    alices_orphan = await harness.upload(ALICE, hours_ago=old)

    await harness.sweep().execute()

    assert bobs in harness.photos.objects
    assert alices_orphan not in harness.photos.objects


async def test_a_photo_dropped_from_a_profile_becomes_sweepable():
    """Uploaded and committed, then replaced from the profile screen.

    The reference is the *current* photo list, not "was ever named" — a photo no
    profile points at is the same orphan whether it was never committed or is no
    longer committed, and it is unreachable either way.
    """

    harness = Harness()
    old = UNCOMMITTED_PHOTO_RETENTION_HOURS + 2
    dropped = await harness.upload(ALICE, hours_ago=old)
    replacement = await harness.upload(ALICE, hours_ago=old)
    await harness.commit_profile(ALICE, dropped)

    profile = await harness.profiles.load(ALICE)
    assert profile is not None
    profile.change_photos([replacement.photo_id], occurred_at=instant(NOW))
    await harness.profiles.save(profile)

    await harness.sweep().execute()

    assert replacement in harness.photos.objects
    assert dropped not in harness.photos.objects


async def test_an_owner_with_no_profile_at_all_loses_every_old_photo():
    """*No profile yet* is the ordinary state of an abandoned onboarding, and
    the repository answers it with `None` rather than a raise."""

    harness = Harness()
    old = UNCOMMITTED_PHOTO_RETENTION_HOURS + 2
    refs = [await harness.upload(ALICE, hours_ago=old) for _ in range(3)]

    report = await harness.sweep().execute()

    assert harness.photos.objects == {}
    assert sorted(harness.photos.deletions, key=str) == sorted(refs, key=str)
    assert report.deleted == 3


# ---------------------------------------------------------------------------
# Idempotent, and safe beside itself
# ---------------------------------------------------------------------------


async def test_a_second_sweep_finds_nothing_left_to_do():
    harness = Harness()
    await harness.upload(ALICE, hours_ago=UNCOMMITTED_PHOTO_RETENTION_HOURS + 1)

    first = await harness.sweep().execute()
    second = await harness.sweep().execute()

    assert (first.examined, first.deleted) == (1, 1)
    assert (second.examined, second.deleted) == (0, 0)


async def test_a_sweep_that_lost_the_race_still_finishes():
    """The concurrent case: another sweep deleted the object between the listing
    and this one's delete. The store answers *gone* to both, and neither raises —
    which is why two of these may run at once with no lock between them."""

    harness = Harness()
    orphan = await harness.upload(
        ALICE, hours_ago=UNCOMMITTED_PHOTO_RETENTION_HOURS + 1
    )
    sweep = harness.sweep()

    # The rival, run to completion first: everything this sweep is about to be
    # handed has already been deleted.
    await harness.sweep().execute()
    report = await sweep.execute()

    assert orphan not in harness.photos.objects
    assert report.deleted == 0


async def test_a_profile_is_replayed_once_per_owner_not_once_per_photo():
    """Three photos under one owner, one replay.

    A profile stream grows for years (`domain/profile.py`), so a sweep that
    replayed one per candidate would cost the corpus times the stream — and
    nothing about its deletions would look different.
    """

    harness = Harness()
    old = UNCOMMITTED_PHOTO_RETENTION_HOURS + 2
    for _ in range(3):
        await harness.upload(ALICE, hours_ago=old)

    harness.profiles.loaded.clear()
    await harness.sweep().execute()

    assert harness.profiles.loaded == [ALICE]


async def test_a_failure_mid_walk_closes_the_listing_rather_than_abandoning_it():
    """The listing holds an open store client across its yields.

    A delete that raises must not leave that client to be finalised whenever the
    event loop gets round to it — the job above swallows the failure and ticks
    again, so an abandoned generator would be one leaked client per failed run
    rather than one ever.
    """

    harness = Harness()
    for _ in range(3):
        await harness.upload(ALICE, hours_ago=UNCOMMITTED_PHOTO_RETENTION_HOURS + 2)

    closed: list[bool] = []
    listing = harness.photos.stored_before

    async def watched(cutoff):
        try:
            async for photo in listing(cutoff):
                yield photo
        finally:
            closed.append(True)

    harness.photos.stored_before = watched

    async def refuse(ref):
        raise RuntimeError("the object store was unreachable")

    harness.photos.delete = refuse

    with pytest.raises(RuntimeError):
        await harness.sweep().execute()

    assert closed == [True], "the listing was abandoned without being closed"
