"""Commit every answer from onboarding's second part, in one transaction.

**One request, one transaction, one profile.** The six social steps are a
client-held draft and nothing is written until the part ends
(``docs/adr/0090``), so this is the only write in it — and it either records
every answer or none of them.

**Every rule the client enforced is re-validated here.** The tag vocabulary, the
floor and the ceiling, the radius bounds: all three are served so a picker can
build a control that cannot produce an illegal value, and a control is not a
validation (``docs/adr/0089``). A replayed request, an older build and a script
are all clients too. The photo ids are re-validated the same way and against the
same port the upload used, because an id a player never uploaded — or one
belonging to somebody else — must be refused rather than stored as a dangling
reference no later read can explain.

**Idempotency is answered from the stream, not from a table beside it.** The
creating event carries the key the commit was made under, so *has this exact
request already been served* is a question the aggregate can answer about itself.
The alternative — an ``idempotency_keys`` table written in the same transaction —
is a second record of one fact and so a second place for it to disagree, which is
the dual-write shape ADR-0017 rejected and ADR-0089 declined to reintroduce for
the consent record.

A second commit with a **different** key is not a retry; it is a second attempt
at a part that happens once, and it is refused. Editing an existing profile is
the profile screen's job and a different request.

**A genuinely concurrent duplicate loses a race rather than replaying.** Two
requests carrying the same key that both read an empty stream before either
appends compute the same stream id, collide on version 1 and the store rejects
the loser — which surfaces as ``concurrent_modification``, the client retries,
and the retry replays. That is the same trade ``next_identity`` makes for
concurrent assessment starts (#35): the store's uniqueness is what guarantees one
profile, and recovering inside a poisoned transaction to save one round trip is
not worth the complexity.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant
from app.modules.player_profile.application.commands import (
    CommitPlayerProfileCommand,
)
from app.modules.player_profile.domain.availability import AvailabilityGrid
from app.modules.player_profile.domain.errors import (
    PhotoNotFound,
    PlayerProfileAlreadyExists,
    ProposalsOptInNotAnswered,
)
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.photos import PhotoRef
from app.modules.player_profile.domain.ports import (
    PhotoStorage,
    PlayerProfileRepository,
)
from app.modules.player_profile.domain.profile import PlayerProfile, photo_order
from app.modules.player_profile.domain.search_radius import SearchRadius
from app.modules.player_profile.domain.social_tags import SocialTagSelection


@dataclass(frozen=True, slots=True)
class CommittedPlayerProfile:
    """The profile, and whether this request is what created it.

    ``created`` exists so the boundary can answer 201 for the commit and 200 for
    its replay. The **body is the same either way**, so a client that only wants
    its profile needs no branch; the status is there for one that wants to tell
    the two apart, exactly as a repeated assessment start does.
    """

    profile: PlayerProfile
    created: bool


class CommitPlayerProfile:
    def __init__(
        self,
        *,
        profiles: PlayerProfileRepository,
        photos: PhotoStorage,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._profiles = profiles
        self._photos = photos
        self._uow = uow
        self._clock = clock

    async def execute(
        self, command: CommitPlayerProfileCommand
    ) -> CommittedPlayerProfile:
        existing = await self._profiles.load(command.player_id)
        if existing is not None:
            # The whole of idempotency, and it needs nothing but the stream. A
            # matching key means this request has already been served, so the
            # first commit's profile is returned unchanged — not re-derived, not
            # re-recorded.
            if existing.idempotency_key == command.idempotency_key:
                return CommittedPlayerProfile(profile=existing, created=False)
            raise PlayerProfileAlreadyExists()

        # The pure refusals first, cheapest and most likely, before anything
        # asks the object store a question. A commit that was going to be
        # refused for its tags should not cost three round trips first.
        if command.proposals_opt_in is None:
            raise ProposalsOptInNotAnswered()

        selection = SocialTagSelection.from_ids(command.social_tag_ids)
        radius = SearchRadius.chosen(command.search_radius_km)
        area = LocationArea.around(command.latitude, command.longitude)
        grid = AvailabilityGrid.of_cells(command.availability)
        # Ordered and counted here as well as inside ``create``, so that the
        # ids checked against storage below are exactly the ids that will be
        # recorded — a duplicate refused after three existence checks would have
        # been three checks nobody needed.
        photo_ids = photo_order(command.photo_ids)

        for photo_id in photo_ids:
            # Through the same port and the same ``PhotoRef`` the upload used, so
            # ownership is the port's contract rather than a check written twice.
            # Another player's photo id answers exactly as an imaginary one does.
            found = await self._photos.exists(
                PhotoRef(owner_id=command.player_id, photo_id=photo_id)
            )
            if not found:
                raise PhotoNotFound()

        now = self._now()
        profile = PlayerProfile.create(
            player_id=command.player_id,
            social_tags=selection,
            photo_ids=photo_ids,
            availability=grid,
            location=area,
            search_radius=radius,
            gender=command.gender,
            gender_preference=command.gender_preference,
            proposals_opt_in_accepted=command.proposals_opt_in,
            consent_copy_version=command.consent_copy_version,
            consent_surface=command.consent_surface,
            idempotency_key=command.idempotency_key,
            occurred_at=now,
        )

        # One clock read, two events, one transaction. The creation and the
        # consent answer are the same moment because they *are* the same act.
        await self._profiles.save(profile)
        await self._uow.commit()

        return CommittedPlayerProfile(profile=profile, created=True)

    def _now(self) -> Instant:
        return instant(self._clock.now())
