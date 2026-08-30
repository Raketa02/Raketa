"""The four fail-closed gates, re-verified live over a whole court.

**Five facts are re-verified when a challenge is minted, and four of them are
here.** They are the ones ``read_back_search`` already re-evaluates on a stored
search — a block either way, a hold, an account ``users`` may not show, and the
mutual gender preference — and they are re-read because the court may have been
built an hour ago and nothing in Play background-refetches. The fifth is the
open-challenge pair rule, which is a statement about *other challenges* and lives
with the use case that holds that read.

**It answers a boolean, and the shape is the disclosure rule made structural.**
There is no method here that returns who failed, so no caller can put a person in
a refusal even by accident: ``docs/adr/0130`` admits exactly one field against
*nobody may ask who was withheld*, and the single exemption is what keeps it a
rule. The organiser finds out who by re-reading the origin search, which
re-evaluates these same four gates and marks the rows it withholds — identical
outcome, zero new disclosure.

**Every gate binds every pair on the court** (``docs/adr/0116``). A four contains
six pairs and the organiser is in only three of them, so a send that checked only
the organiser's own three would seat two people together across a block neither
of them could see. The pairwise gates therefore run over the whole court and the
per-person gates over everybody on it.

**No ``GateCode`` is spelled here, and that is deliberate.** ``GateCode`` is a
*search* vocabulary — a histogram over ten codes, counted in declaration order —
and re-spelling it in this context would be two closed vocabularies for one set
of facts. What crosses out of here is *admitted* or *not*.

**The reading is live and stays live.** The send reads profiles from
``player_profile`` while the read-back reads the index, so the two can differ —
most plausibly on the mutual preference. Moving the send onto the index to close
that gap would buy a rare confusing screen at the price of a safety gate
inheriting index staleness, which is the wrong direction on the one class of
check that must not be stale.
"""

from __future__ import annotations

from functools import partial
from itertools import combinations
from typing import Awaitable, Callable, Collection, Mapping, TypeVar, final
from uuid import UUID

from app.modules.blocks.domain.ports import BlockQuery
from app.modules.challenges.domain.errors import TheGatesCouldNotBeEvaluated
from app.modules.challenges.domain.ports import AccountHoldQuery
from app.modules.player_profile.domain.mutual_preference import (
    preferences_are_mutual,
)
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.users.domain.ports import UserRepository

_T = TypeVar("_T")


@final
class CourtSafety:
    """*May these people be put on a court together, right now?*

    Four collaborators and four gates. Three of them are the provider's own port
    — ``blocks`` and ``users`` ship theirs, and a profile is read through
    ``player_profile``'s repository — and the fourth, the hold, is this context's
    own declaration against a provider that does not exist.
    """

    def __init__(
        self,
        *,
        blocks: BlockQuery,
        holds: AccountHoldQuery,
        accounts: UserRepository,
        profiles: PlayerProfileRepository,
    ) -> None:
        self._blocks = blocks
        self._holds = holds
        self._accounts = accounts
        self._profiles = profiles

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        """Which of these accounts are under a live hold.

        The one read here that answers with people rather than with a verdict,
        and the only caller allowed to use it is the one refusing **you** your
        own send: a hold that stops you searching but lets you send invitations
        is that hole with the blast radius pointed at other people. Nothing about
        anybody else may be read off it.
        """

        return await self._read(lambda: self._holds.held_among(player_ids), "the hold")

    async def admits(self, court: Collection[UUID]) -> bool:
        """Whether every gate admits every pair of this court.

        Reads first and judges afterwards, so one press costs four reads whatever
        the answer is — a short-circuit would make *which gate refused* readable
        from the latency, which is the same disclosure by a slower route.
        """

        players = frozenset(court)
        blocked = await self._read(
            lambda: self._blocks.blocked_pairs_among(players), "the block mask"
        )
        held = await self._read(
            lambda: self._holds.held_among(players), "the hold"
        )
        unshowable = await self._read(
            lambda: self._accounts.find_disabled_among(players), "the account state"
        )
        profiles = await self._profiles_of(players)
        return (
            not blocked
            and not held
            and not unshowable
            and self._preferences_hold(players, profiles)
        )

    def _preferences_hold(
        self, players: frozenset[UUID], profiles: Mapping[UUID, PlayerProfile]
    ) -> bool:
        """The mutual gender gate, over every pair on the court.

        A player with no profile has no preference to read, which is a gate that
        **cannot be evaluated** — and a gate that cannot be evaluated excludes.
        That is not a hypothetical here: a court is built out of an index whose
        rows outlive the profiles they were folded from.
        """

        for one, other in combinations(sorted(players), 2):
            mine = profiles.get(one)
            theirs = profiles.get(other)
            if mine is None or theirs is None:
                return False
            if not preferences_are_mutual(
                one_gender=mine.gender,
                one_preference=mine.gender_preference,
                other_gender=theirs.gender,
                other_preference=theirs.gender_preference,
            ):
                return False
        return True

    async def _profiles_of(
        self, players: frozenset[UUID]
    ) -> Mapping[UUID, PlayerProfile]:
        """Every profile on the court, read live, one per seat.

        A read per player rather than a set read, because that is the shape
        ``PlayerProfileRepository`` has: it is keyed on the player and nothing
        else, which is the hazard-closing shape the profile context chose long
        before anybody wanted four of them at once. A court is four people, so
        this is four reads on a send and never a scan.
        """

        found: dict[UUID, PlayerProfile] = {}
        for player_id in sorted(players):
            profile = await self._read(
                partial(self._profiles.load, player_id), "a profile"
            )
            if profile is not None:
                found[player_id] = profile
        return found

    async def _read(self, read: Callable[[], Awaitable[_T]], what: str) -> _T:
        """One gate read, under the posture every gate here declares: **closed**.

        Somebody else's outage becomes this context's own refusal — a 503 about
        the platform rather than a 409 about the court — which is the same
        translation ``live_block_set`` performs one context over, and it is
        written once here for the reason it is written once there: a safety gate
        translated in one place and swallowed in another is the failure the
        fail-closed rule exists to prevent.
        """

        try:
            return await read()
        except TheGatesCouldNotBeEvaluated:
            raise
        except Exception as failure:
            raise TheGatesCouldNotBeEvaluated(
                f"{what} could not be evaluated"
            ) from failure
