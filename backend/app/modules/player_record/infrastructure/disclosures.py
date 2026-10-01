"""The four things that entitle a reader to a record, one adapter each.

Four implementations of one port, in the **consumer's** infrastructure — the
shape ``sportsmanship`` takes over ``games``' directory, and for the same reason:
a provider publishes what it knows about its own subject, and the context that
wants it narrower does the narrowing. *Have I been shown this person* does not
become a method on somebody else's port.

**Each answers in sports and never in ids.** What the caller needs is a
partition to re-evaluate the four fail-closed gates in, and a search id, a
challenge id, a game id or a group id would be an identifier this answer is not
about — and one more thing on a refusal path that is supposed to say nothing.

**They are four because the entitlements are four, not because the stores
are.** The fourth is the one the others anticipated: a group's Members is a
surface that shows one player to another and is not a search, so it satisfied
this same demand with a fourth row in the register, and this context never
learned what a group is. A fifth would do the same.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.challenges.domain.ports import ChallengeDirectory
from app.modules.challenges.domain.standing import ENDED
from app.modules.games.domain.ports import GameDirectory
from app.modules.groups.domain.ports import GroupDirectory
from app.modules.matchmaking.domain.search_store import SearchStore


@final
class SearchesThatShowedThem:
    """``PriorDisclosure`` over the search record. **The first strand.**

    *The subject was returned by a search of the reader's* — read from the one
    place that fact is already written down rather than recomputed: the
    ``RETURNED`` rows of the reader's own searches (``docs/adr/0104``).

    **The radar's reading is the fourth surface that introduces one player to
    another, and it rides on this strand rather than adding one**
    (``docs/adr/0174`` §1). A reading is a recorded search with ``RETURNED``
    rows, and the read below asks for no surface — so the sheet opens from
    every card a reading drew by the same rule it opens from a shortlist's,
    and a fourth register row over this same adapter would be the first row
    twice. The fourth *row* ADR-0159 §3 anticipated is for a surface that is
    not a search, and a group's Members is the first (``GroupsTheyShare``).
    """

    def __init__(self, searches: SearchStore) -> None:
        self._searches = searches

    async def partitions_between(
        self, *, reader_id: UUID, subject_id: UUID, now: Instant
    ) -> frozenset[Sport]:
        """Every sport a search of this reader's has shown this person in.

        **``now`` is ignored, and that is the decision rather than an
        oversight.** A search record never expires, so there is no window to
        apply and nothing here folds against a clock: an expiry shorter than
        *for ever* could only refuse a face the app is currently showing, from a
        shortlist the reader can still open.
        """

        return await self._searches.sports_shown_in(
            searcher_id=reader_id, player_id=subject_id
        )


@final
class ChallengesTheyShare:
    """``PriorDisclosure`` over ``challenges``' directory. **The second strand.**

    This is the strand that works the *other* way round from a search. A court is
    sent off the organiser's search, so the organiser has been shown the invitee
    and the invitee has been shown nothing at all — without this, the one person
    who most obviously needs to know who they have been asked to play with could
    not open their record.
    """

    def __init__(self, challenges: ChallengeDirectory) -> None:
        self._challenges = challenges

    async def partitions_between(
        self, *, reader_id: UUID, subject_id: UUID, now: Instant
    ) -> frozenset[Sport]:
        """Every sport in which the pair are both seated in a live challenge.

        **Not ended**, which is the widest of ``challenges``' three readings and
        the right one here: a completed line-up has stopped *arranging* and is
        very much still a game these two are about to play together. A challenge
        that declined or lapsed has ended, and the seat it held is somebody
        else's to be offered — so it entitles nobody, and the sender still holds
        the search that made it.

        The standing is folded against ``now`` rather than read off a column,
        because there is no column: a standing is derived from the seats and the
        clock, and a copy would be wrong for the whole gap between a deadline and
        a sweep.
        """

        return frozenset(
            challenge.sport
            for challenge in await self._challenges.seating(reader_id)
            if challenge.standing_at(now) not in ENDED
            and challenge.seat_of(subject_id) is not None
        )


@final
class GamesTheyPlayed:
    """``PriorDisclosure`` over ``games``' directory. **The third strand.**

    An evening two people were on a court for, and it does not stop having
    happened. There is no window here and no standing test: a game that was
    ghosted, played, scored or argued over is a game the platform put these two
    in front of each other for.
    """

    def __init__(self, games: GameDirectory) -> None:
        self._games = games

    async def partitions_between(
        self, *, reader_id: UUID, subject_id: UUID, now: Instant
    ) -> frozenset[Sport]:
        """Every sport the pair have shared a court in.

        **It asks *which games are mine* and never *which game is this*.** The
        directory answers about one player, so a court the reader was not on is
        not reachable through this read at all — the entitlement is the shape of
        the query rather than a check somebody remembered to write.

        ``now`` is ignored: nothing about *were we both on this court* moves with
        the clock.
        """

        return frozenset(
            game.sport
            for game in await self._games.playing(reader_id)
            if subject_id in game.line_up.players
        )


@final
class GroupsTheyShare:
    """``PriorDisclosure`` over ``groups``' directory. **The fourth strand.**

    A group's Members lists everybody in it who plays the sport — face, name,
    Level, score — and promises *Press and hold anyone for the full record*
    (#514). A member who never searched has been shown every one of them by the
    group and by nothing else, so without this strand the promise was
    ``record_unavailable`` for everybody but themselves (#529).

    **Membership as it stands, never as it was.** A game does not stop having
    happened; a group left is simply no longer one the pair are in, and Members
    stops listing whoever left. A Join request that waits is not membership
    either: the Owner reads the queue, and nothing there opens a record.
    """

    def __init__(self, groups: GroupDirectory) -> None:
        self._groups = groups

    async def partitions_between(
        self, *, reader_id: UUID, subject_id: UUID, now: Instant
    ) -> frozenset[Sport]:
        """**Every sport**, when the pair are both in a group right now.

        Members is read for any sport and lists a member in each one they are
        rated in, so the group has shown them in every partition they have a row
        in — and the admission loop finds that partition by running the gates,
        where a partition with no row for them cannot be evaluated and excludes.
        That costs at most four gate evaluations, which is the bound
        ``RecordAdmission`` already states.

        **Two reads of one player's memberships each, and never a listing.**
        What the pair share is the intersection of the groups each is in, which
        says nothing about who else is in them. ``now`` is ignored: the
        projection is membership as it stands.
        """

        shared = set(await self._groups.groups_of(reader_id)) & set(
            await self._groups.groups_of(subject_id)
        )
        return frozenset(Sport) if shared else frozenset()


__all__ = [
    "ChallengesTheyShare",
    "GamesTheyPlayed",
    "GroupsTheyShare",
    "SearchesThatShowedThem",
]
