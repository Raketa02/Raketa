"""The proposer: which games the engine builds, and who they are dealt to — the
rules that need no I/O (the mechanics §4.3, §5, §6.2–§6.3, §7, §19; the screens
C3; #540).

**One batch is one pool in one sport at one instant.** Everything it reads is
handed in — the members with their weekly hours, Levels, intents and limits, the
pair rule as a mask, where the pool may play, the court hours on sale and the
proposals still filling — and everything it decides comes back as a value: the
cards that **lost** their court hour, the **picks** to make and the **deals** to
add to games already filling. The job applies it through the dealer's own acts,
which refuse whatever changed in between.

**What is new is the assembly, never the scoring** (§5.1, ``docs/adr/0189`` §2):
*who may share a court* is the matcher's pair rule — blocks, mutual gender
preference, the kind's level window — arriving as the ``PlayerFit`` mask, one
per kind, exactly as a line-up's does (``docs/adr/0116``); *how even* is the
engine's own ``forecast`` over the arrangements a card could stand in, the number
the card will print. The forecast is a whole percent and saturates for two equal
sides, so a tie goes to **the closest Levels**, then to whoever joined first.
**Distance stands down inside a pool**: everybody plays at the same clubs.

**A court hour is dealt the most even four (or two)** of the members who may
play it: rated in the sport, wanting the kind, free for the whole hour, able to
afford it, with no game then and a week under their cap — and who fit every
pair among them. As many cards as the club has courts free at
that hour, **of either kind**, each for different people, and **never the same
people twice in one batch**: hours are walked soonest first, so a four is dealt
at its best hour and the next hour deals the next best, and within an hour the
Competitive segment is dealt before the For fun one — somebody wanting either is
on one card at that hour, never one in each segment. Past
``CONSIDERED_AT_AN_HOUR`` members free at once, the ones holding the fewest
cards are considered. A four already on a card together, a court hour already
holding its cards, and a person already on a card at that hour are not dealt
again, which is what makes a batch safe to repeat.

**Where** (§4.3): a player group's home club first, then the other clubs it
plays at, nearest first — at the same hour the home club's court wins. An
official group plays at its own club only, unless the club lets other clubs'
courts serve its groups, and then only for players who share **no** hour at its
own club in the fourteen days. A paused club deals no new card, fourteen days is
the horizon, and the clubs' order and distances are the caller's.

**Dealing a game still filling** (§6.2–§6.3, §7): **every seat a no left goes
to up to three next best fits**, dealt into the version it was on — a name
dealt first who said no, left the pool or stopped fitting somebody In leaves
one, a fit who said no is replaced, and a fit who said yes took it. **In
singles each fit is a version**, so a seat a no left goes to one. **At half its
seats In, a pick widens**: while somebody named has not swiped, its open seats
go out as new versions, up to three in all. A next best fit fits everybody In
and everybody dealt with them, which is what the dealer refuses otherwise; they
are ranked by the forecast of the card they would see.

**A post** (#546; §7, §9.2) is dealt **to whom it is for** — its *Who* and
the range of the others' Levels, and on *Mixed pairs* never more than two of
either gender on a card. At posting it goes to the poster's best fits free at
its hour, one version per **full set** of them, the evenest first, up to three
— or, short of a set, one version with seats open (``versions_of_a_post``).
After, **it keeps being dealt until its book-by** and needs nobody In to widen:
a version naming fewer than its open seats takes whoever **becomes** a fit, a
new full set of fits is a new version while there are fewer than three, and a
seat a no left goes to the next best fits as a pick's does — of the gender it
left, on *Mixed pairs*.

**A lost court hour** (§5.2, §19): a card is lost when **no court is left** at
its club and hour — booked, closed, no longer offered, or the club no longer
selling — and never because the club moved its deadlines, since a card keeps
the book-by it was made with; a paused club's cards keep their court. **The
people who were In are dealt a new card first**, at the nearest hour they are
all free, the same hour at another club it plays at before any other hour,
completed by their best fits. Nobody's yes carries over: a yes is to a court at
an hour.

**On request** (#543; the mechanics §16.8): a full game waiting for its club
**holds its own court** through its request — so it is never lost because that
court is gone from the hour, and never counted as a second card on it — and a
game its club **turned down** is *owed*: its people are dealt a new card first,
exactly as a lost card's are, **never at the club and hour that turned them
down** — by the first batch that finds them an hour, until its own hour has
passed.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from itertools import combinations, groupby
from typing import Final, final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import BalanceRules
from app.engines.matchfit.scorable import LevelReading
from app.engines.matchfit.v1 import forecast
from app.kernel import SPORT_SPECS, Instant, Sport, invariant
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.matchmaking.domain.balance import combine_group_sigma
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.weekly_hours import (
    WeeklyHours,
    free_for_the_hour,
)
from app.modules.proposals.domain.deck import (
    DECK_HORIZON,
    capped_weeks,
    hour_taken,
    named_on,
    week_of,
    weeks_ahead,
)
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.limits import (
    NEXT_BEST_FITS_PER_SEAT,
    VERSIONS_PER_PROPOSAL,
)
from app.modules.proposals.domain.post import PostedFor, Who, stand_together
from app.modules.proposals.domain.proposal import Origin, Proposal, Standing

#: How far ahead the engine deals (the mechanics §4.3) — the deck's horizon,
#: since a deck holds exactly what the engine dealt.
HORIZON: Final = DECK_HORIZON

#: How many of the members free at an hour a game is chosen among. **Domain,
#: never configuration**: which four are dealt is behaviour a player sees. Up to
#: it, the four is the most even of everybody free; past it — a big official
#: group's evening — the members holding the fewest cards are the ones
#: considered, so a big group's cards spread over its people rather than going
#: to the same evenest few at every hour, and the walk over every four stays a
#: few thousand sets however large the group grows.
CONSIDERED_AT_AN_HOUR: Final = 12


# --------------------------------------------------------------------------- #
# What a batch reads
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class Member:
    """One member of the pool, as the proposer reads them for one sport."""

    player_id: UUID
    #: Their Level and Uncertainty in the sport, off rating — ``None`` while
    #: unrated there, which deals them nothing.
    level: LevelReading | None
    week: WeeklyHours
    #: The kinds of game their Play intent wants — empty while undeclared.
    wants: frozenset[SearchMode]
    #: Their Games & money: games per week and most I'll pay.
    limits: GamesAndMoney
    #: When each game they have booked starts.
    booked: tuple[Instant, ...] = ()
    #: Their gender and gender preference, read only for whom a post is for
    #: (#546) — ``None`` where it cannot be read, which a post for anybody but
    #: *Anyone* does not take.
    gender: Gender | None = None
    preference: GenderPreference | None = None


def capped_weeks_of(member: Member, *, now: Instant) -> frozenset[date]:
    """The Mondays of the weeks a card dealt now could be in that hold as many
    of this member's games as they allow."""

    return frozenset(
        week.starts_on
        for week in capped_weeks(
            weeks_ahead(now), member.booked, games_per_week=member.limits.games_per_week
        )
    )


def may_play(
    member: Member,
    kind: SearchMode,
    *,
    start: Instant,
    share_grosze: int | None,
    capped: frozenset[date],
) -> bool:
    """Whether this member may be dealt a game of ``kind`` from ``start`` at
    ``share_grosze`` a seat — ``None`` where no court, and so no price, is
    asked about: rated, wanting the kind, the share within their *most I'll
    pay*, a week under their cap (``capped``), no game then, and free for the
    whole hour."""

    return (
        member.level is not None
        and kind in member.wants
        and (share_grosze is None or member.limits.shows(share_grosze=share_grosze))
        and week_of(start) not in capped
        and not hour_taken(start, member.booked)
        and free_for_the_hour(member.week, start=start, zone=CLUB_ZONE)
    )


def admitted(posted_for: PostedFor | None, member: Member) -> bool:
    """Whether a post is for this member — every member, on a pick."""

    return posted_for is None or posted_for.admits(
        level=None if member.level is None else member.level.mu,
        gender=member.gender,
        preference=member.preference,
    )


@final
@dataclass(frozen=True, slots=True)
class CourtHourOnSale:
    """An hour a club sells through Raketa in the sport: how many of its courts
    are free then, the share fixed on a card made now, and its book-by."""

    club_id: UUID
    sport: Sport
    start: Instant
    courts: int
    share_grosze: int
    book_by: Instant
    #: ``False`` while the club is paused: its cards keep their court, and no
    #: new card is built on it.
    taking_new_cards: bool = True

    def __post_init__(self) -> None:
        invariant(self.courts >= 1, f"{self.courts} courts on sale at {self.start}")


@final
@dataclass(frozen=True, slots=True)
class PoolClubs:
    """Where a pool may play: its home club, and the other clubs it may use,
    nearest first."""

    home_club_id: UUID
    others: tuple[UUID, ...] = ()
    #: An official group's: another club's court only for players who share no
    #: hour at the home club (the mechanics §4.3).
    others_only_when_home_is_full: bool = False

    @property
    def home_first(self) -> tuple[UUID, ...]:
        """Every club the pool plays at, home first."""

        return (self.home_club_id, *self.others)

    def rank_of(self, club_id: UUID) -> int | None:
        """``0`` for the home club, the others after it in order, and ``None``
        for a club it does not play at."""

        if club_id == self.home_club_id:
            return 0
        if club_id in self.others:
            return 1 + self.others.index(club_id)
        return None


# --------------------------------------------------------------------------- #
# What a batch decides
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class Pick:
    """A game to make: a *Picked for you* card at a club and hour, named for
    its people — in the order they are dealt."""

    kind: SearchMode
    club_id: UUID
    start: Instant
    named: tuple[UUID, ...]
    #: The card that lost its court hour, whose people In this is dealt to
    #: first; ``None`` for a fresh pick.
    after: UUID | None = None


@final
@dataclass(frozen=True, slots=True)
class Deal:
    """More people for a game still filling: ``into`` a version, as next best
    fits for the seats its noes left, or — ``None`` — as a new version."""

    proposal_id: UUID
    players: tuple[UUID, ...]
    into: int | None


@final
@dataclass(frozen=True, slots=True)
class Batch:
    """One pool's batch, in the order it is applied: the cards that lost their
    court hour, the picks — those dealt to the people In on a lost card or a
    turned-down game first — the turned-down games now done with, and the
    deals."""

    lost: tuple[UUID, ...] = ()
    picks: tuple[Pick, ...] = ()
    #: Every owed game whose people this batch dealt a new card first. One it
    #: found no hour for stays owed, for the next batch to look again.
    redealt: tuple[UUID, ...] = ()
    deals: tuple[Deal, ...] = ()


def propose(
    *,
    sport: Sport,
    members: Sequence[Member],
    unfit: Mapping[SearchMode, Collection[frozenset[UUID]]],
    clubs: PoolClubs,
    hours: Sequence[CourtHourOnSale],
    held: Collection[tuple[UUID, Instant]],
    filling: Sequence[Proposal],
    balance: BalanceRules,
    now: Instant,
    owed: Sequence[Proposal] = (),
) -> Batch:
    """The batch for one pool in one sport at ``now``.

    ``members`` in the pool's own order — who joined first breaks a tie;
    ``unfit`` every pair that may not share a court, per kind; ``hours`` what
    the clubs the pool plays at sell in the sport now (a paused club's
    included); ``held`` every club and hour of the sport a court is still there
    for, **whatever deadline the club's settings now give it** — a card lives to
    its own book-by, and loses its court hour only when no court is left;
    ``filling`` this pool's proposals in the sport still filling at ``now``; and
    ``owed`` its games in the sport a club turned down whose people have not
    been dealt a new card yet."""

    return _Batching(
        sport=sport,
        members=members,
        unfit=unfit,
        clubs=clubs,
        hours=hours,
        held=held,
        filling=filling,
        owed=owed,
        balance=balance,
        now=now,
    ).run()


def versions_of_a_post(
    *,
    sport: Sport,
    members: Sequence[Member],
    unfit: Collection[frozenset[UUID]],
    poster: UUID,
    kind: SearchMode,
    hour: CourtHourOnSale,
    posted_for: PostedFor,
    balance: BalanceRules,
    now: Instant,
) -> tuple[tuple[UUID, ...], ...]:
    """The names a post is dealt to when it is posted (the mechanics §9.2):
    **one version per full set** of the poster's best fits free at ``hour``,
    the evenest first, up to three — each fitting the poster and each other —
    or, with no full set, **one version with as many as fit**, its other seats
    open. ``members`` the pool in its own order, the poster among them;
    ``unfit`` every pair that may not share a court in ``kind``."""

    return _Batching(
        sport=sport,
        members=members,
        unfit={kind: unfit},
        clubs=PoolClubs(home_club_id=hour.club_id),
        hours=(),
        held=(),
        filling=(),
        owed=(),
        balance=balance,
        now=now,
    ).versions_of_a_post(poster, kind, hour=hour, posted_for=posted_for)


# --------------------------------------------------------------------------- #
# The batch
# --------------------------------------------------------------------------- #

#: A score for a set of people: the forecast of its evenest arrangement, then
#: how close its Levels are (a narrower spread is a larger score).
_Score = tuple[int, float]

#: A set of members, as a bit per member in the pool's order — what the walk
#: over every four is done in, since a four is asked about thousands of times
#: a batch and an ``int`` is the cheapest set there is to hash and intersect.
_Members = int


class _Batching:
    def __init__(
        self,
        *,
        sport: Sport,
        members: Sequence[Member],
        unfit: Mapping[SearchMode, Collection[frozenset[UUID]]],
        clubs: PoolClubs,
        hours: Sequence[CourtHourOnSale],
        held: Collection[tuple[UUID, Instant]],
        filling: Sequence[Proposal],
        owed: Sequence[Proposal],
        balance: BalanceRules,
        now: Instant,
    ) -> None:
        self._seats = SPORT_SPECS[sport].players
        self._per_side = self._seats // 2
        self._members = {member.player_id: member for member in members}
        invariant(len(self._members) == len(members), "a member listed twice")
        self._ids = tuple(member.player_id for member in members)
        self._index = {player: index for index, player in enumerate(self._ids)}
        #: Each member's Level — a placeholder for the unrated, who are never
        #: considered, so a score never reads one.
        self._levels = tuple(
            member.level or LevelReading(mu=0.0, sigma=0.0) for member in members
        )
        self._unfit = {kind: frozenset(unfit.get(kind, ())) for kind in SearchMode}
        #: Per kind, per member: everybody they may share a court with.
        self._fitting: dict[SearchMode, list[_Members]] = {}
        for kind in SearchMode:
            fitting = [0] * len(self._ids)
            for one, other in combinations(range(len(self._ids)), 2):
                if self._fits(kind, self._ids[one], self._ids[other]):
                    fitting[one] |= 1 << other
                    fitting[other] |= 1 << one
            self._fitting[kind] = fitting
        self._clubs = clubs
        self._balance = balance
        self._capped: dict[UUID, frozenset[date]] = {
            member.player_id: capped_weeks_of(member, now=now) for member in members
        }
        self._genders = {member.player_id: member.gender for member in members}

        for hour in hours:
            invariant(hour.sport is sport, f"a {hour.sport} hour in a {sport} batch")
        for proposal in filling:
            invariant(
                proposal.sport is sport
                and proposal.standing_at(now) is Standing.FILLING,
                f"{proposal.proposal_id} is not a {sport} game filling at {now}",
            )
        for proposal in owed:
            invariant(
                proposal.sport is sport and proposal.owes_a_new_card,
                f"{proposal.proposal_id} owes no {sport} card",
            )
        ordered = sorted(filling, key=lambda p: (p.start, str(p.proposal_id)))
        still_held = frozenset(held)
        # A game waiting for its club holds its court through its request, so
        # the court gone from the hour is its own.
        self._lost = tuple(
            p
            for p in ordered
            if not p.waiting_for_the_club and (p.club_id, p.start) not in still_held
        )
        self._live = tuple(p for p in ordered if p not in self._lost)
        self._owed = tuple(sorted(owed, key=lambda p: (p.start, str(p.proposal_id))))

        horizon = now + HORIZON
        self._selling = tuple(
            sorted(
                (
                    hour
                    for hour in hours
                    if hour.taking_new_cards
                    and clubs.rank_of(hour.club_id) is not None
                    and now < hour.book_by
                    and hour.start < horizon
                ),
                key=lambda hour: (hour.start, clubs.rank_of(hour.club_id)),
            )
        )
        #: For each hour the home club sells, everybody free for the whole of it.
        self._free_at_home = tuple(
            self._mask(
                player
                for player in self._ids
                if free_for_the_hour(
                    self._members[player].week, start=hour.start, zone=CLUB_ZONE
                )
            )
            for hour in self._selling
            if hour.club_id == clubs.home_club_id
        )

        self._picks: list[Pick] = []
        self._deals: list[Deal] = []
        #: Who this batch put on a card, by hour — of either kind, since one
        #: person at one hour is one game whatever it is called.
        self._dealt_at: dict[Instant, set[UUID]] = {}
        #: The members on each card — a version of a game filling with
        #: everybody In, or a pick of this batch — and, for the question asked
        #: of every candidate four, every full game's worth of them. **Either
        #: kind**: the same four are the same people in both segments.
        self._cards: list[_Members] = []
        self._full_games_on_cards: set[_Members] = set()
        for proposal in self._live:
            for version in proposal.versions:
                self._on_the_cards(self._mask((*proposal.yeses, *version.players)))
        self._scores: dict[_Members, _Score] = {}
        self._ranked: dict[
            tuple[SearchMode, _Members, int, _Members], list[_Members]
        ] = {}
        #: How many cards each member holds — on the games filling, and dealt
        #: by this batch — which decides who is considered at a crowded hour.
        self._holding = {player: 0 for player in self._ids}
        for proposal in self._live:
            for player in {*proposal.yeses, *named_on(proposal)}:
                if player in self._holding:
                    self._holding[player] += 1

    def run(self) -> Batch:
        for proposal in self._lost:
            self._deal_again_to_those_in(proposal)
        redealt = tuple(
            proposal.proposal_id
            for proposal in self._owed
            # Anywhere but where the club turned them down.
            if self._deal_again_to_those_in(
                proposal, not_at=(proposal.club_id, proposal.start)
            )
        )
        for proposal in self._live:
            self._deal_on(proposal)
        # Hour by hour, and within an hour the kinds in the enum's order and
        # the clubs home first: an hour's courts are shared by both kinds.
        for _, hours in groupby(self._selling, key=lambda hour: hour.start):
            at_the_hour = tuple(hours)
            for kind in SearchMode:
                for hour in at_the_hour:
                    self._fill(kind, hour)
        return Batch(
            lost=tuple(proposal.proposal_id for proposal in self._lost),
            picks=tuple(self._picks),
            redealt=redealt,
            deals=tuple(self._deals),
        )

    # ------------------------------------------------------------ fresh picks

    def _fill(self, kind: SearchMode, hour: CourtHourOnSale) -> None:
        """Deal the hour its evenest fours, one per free court, each for
        different people."""

        free_courts = hour.courts - self._picks_at(hour)
        pool = self._pool_at(kind, hour)
        refused = self._refusal(hour)
        while free_courts > 0:
            people = self._evenest(kind, pool, self._seats, refused=refused)
            if people is None:
                return
            self._pick(kind, hour, people)
            pool &= ~self._mask(people)
            free_courts -= 1

    def _deal_again_to_those_in(
        self, lost: Proposal, *, not_at: tuple[UUID, Instant] | None = None
    ) -> bool:
        """The people In on a card that lost its court hour — or a game its
        club turned down, or the people still in a booked game its club
        cancelled (#547) — dealt a new card first: the nearest hour they are
        all free, completed by their best fits — or as many of them as there
        are — and never ``not_at``. Whether a card was dealt."""

        kind = lost.kind
        in_ = tuple(player for player in lost.owed_to if player in self._members)
        if not in_ or not all(
            self._fits(kind, one, other) for one, other in combinations(in_, 2)
        ):
            return False
        nearest = sorted(
            self._selling,
            key=lambda hour: (
                abs(hour.start - lost.start),
                hour.start,
                self._clubs.rank_of(hour.club_id),
            ),
        )
        for hour in nearest:
            if (hour.club_id, hour.start) == not_at:
                continue
            if self._picks_at(hour) >= hour.courts or not all(
                self._may_play(
                    player, kind, start=hour.start, share_grosze=hour.share_grosze
                )
                for player in in_
            ):
                continue
            pool = self._pool_at(kind, hour, besides=in_)
            refused = self._refusal(hour)
            for size in range(self._seats, len(in_) - 1, -1):
                people = self._evenest(kind, pool, size, must=in_, refused=refused)
                if people is not None:
                    self._pick(kind, hour, people, after=lost.proposal_id)
                    return True
        return False

    def _pick(
        self,
        kind: SearchMode,
        hour: CourtHourOnSale,
        people: tuple[UUID, ...],
        *,
        after: UUID | None = None,
    ) -> None:
        self._picks.append(
            Pick(
                kind=kind,
                club_id=hour.club_id,
                start=hour.start,
                named=people,
                after=after,
            )
        )
        self._dealt_at.setdefault(hour.start, set()).update(people)
        self._on_the_cards(self._mask(people))
        self._hold(people)

    def _hold(self, people: Iterable[UUID]) -> None:
        for player in people:
            if player in self._holding:
                self._holding[player] += 1

    def _pool_at(
        self, kind: SearchMode, hour: CourtHourOnSale, *, besides: Sequence[UUID] = ()
    ) -> _Members:
        """Everybody who may be dealt a game of ``kind`` at ``hour`` and is on
        no card then yet — ``besides`` those already named for it."""

        busy = self._on_a_card_at(hour.start)
        return self._mask(
            player
            for player in self._ids
            if player not in busy
            and player not in besides
            and self._may_play(
                player, kind, start=hour.start, share_grosze=hour.share_grosze
            )
        )

    def _on_the_cards(self, people: _Members) -> None:
        self._cards.append(people)
        self._full_games_on_cards.update(
            sum(1 << index for index in game)
            for game in combinations(_indices(people), self._seats)
        )

    # --------------------------------------------------- a game still filling

    def _deal_on(self, proposal: Proposal) -> None:
        if proposal.open_seats == 0:
            return
        kind, in_ = proposal.kind, proposal.yeses
        dealt: set[UUID] = set()
        #: Who this batch dealt into each version.
        dealt_into: dict[int, list[UUID]] = {}

        def may_be_dealt(player: UUID, *, beside: Sequence[UUID] = ()) -> bool:
            """Whether this member may be dealt the game, beside ``beside`` on
            their version."""

            return (
                player not in dealt
                and not proposal.is_on_it(player)
                and self._may_play(
                    player,
                    kind,
                    start=proposal.start,
                    share_grosze=proposal.share_grosze,
                )
                and self._admitted(proposal.posted_for, player)
                and all(self._fits(kind, player, there) for there in in_)
                and self._stand_together(proposal, (*in_, *beside, player))
            )

        # In singles each fit is a version of their own: one per seat a no
        # left. In doubles a seat goes to up to three, the first yes taking it.
        fits_per_seat = 1 if self._per_side == 1 else NEXT_BEST_FITS_PER_SEAT
        for version in proposal.versions:
            first = version.players[: version.first_named]
            later = version.players[version.first_named :]
            # The seats this version's noes left — a name dealt first who said
            # no, left the pool or no longer fits the people In — less those a
            # next best fit has since taken.
            left = min(
                sum(1 for player in first if self._gone(proposal, player))
                - sum(1 for player in later if player in in_),
                proposal.open_seats,
            )
            waiting = [
                player
                for player in later
                if player not in in_ and not self._gone(proposal, player)
            ]
            wanted = fits_per_seat * left - len(waiting)
            if wanted <= 0:
                continue
            holders = self._holders(proposal, version.players)
            # The seats it was dealt for still held: a next best fit stands
            # beside them, so a mixed pair's seat goes to the gender it lost.
            standing = self._holders(proposal, first)
            chosen = self._next_best(
                proposal,
                [p for p in self._ids if may_be_dealt(p, beside=standing)],
                holders=holders,
                wanted=wanted,
            )
            if chosen:
                self._deal(proposal, chosen, into=version.number)
                dealt.update(chosen)
                dealt_into.setdefault(version.number, []).extend(chosen)

        if proposal.origin is Origin.POST:
            self._deal_on_a_post(proposal, may_be_dealt, dealt, dealt_into)
        elif self._widens(proposal):
            self._new_versions(
                proposal,
                may_be_dealt,
                dealt,
                sizes=lambda versions: range(proposal.open_seats, 0, -1),
            )

    def _deal_on_a_post(
        self,
        proposal: Proposal,
        may_be_dealt: Callable[..., bool],
        dealt: set[UUID],
        dealt_into: Mapping[int, Sequence[UUID]],
    ) -> None:
        """A post keeps being dealt until its book-by (the mechanics §9.2):
        a version naming fewer than its open seats takes whoever **became** a
        fit, and a full set of fits is a new version while there are fewer
        than three — or, on a post nobody was dealt, as many as fit."""

        for version in proposal.versions:
            holders = [
                *self._holders(proposal, version.players),
                *dealt_into.get(version.number, ()),
            ]
            room = proposal.open_seats - len(holders)
            if room <= 0:
                continue
            chosen = self._next_best(
                proposal,
                [
                    player
                    for player in self._ids
                    if may_be_dealt(player, beside=holders)
                    and all(
                        self._fits(proposal.kind, player, there) for there in holders
                    )
                ],
                holders=holders,
                wanted=room,
                beside=holders,
            )
            if chosen:
                self._deal(proposal, chosen, into=version.number)
                dealt.update(chosen)
        self._new_versions(
            proposal,
            may_be_dealt,
            dealt,
            sizes=lambda versions: (
                (proposal.open_seats,)
                if versions
                else range(proposal.open_seats, 0, -1)
            ),
        )

    def _next_best(
        self,
        proposal: Proposal,
        candidates: Iterable[UUID],
        *,
        holders: Sequence[UUID],
        wanted: int,
        beside: Sequence[UUID] | None = None,
    ) -> tuple[UUID, ...]:
        """Up to ``wanted`` of ``candidates`` for a version still held by
        ``holders``, the best card first — each fitting the others chosen and,
        given ``beside``, standing with the people In, them and each other."""

        kind, in_ = proposal.kind, proposal.yeses
        ranked = sorted(
            candidates,
            key=lambda player: (
                _descending(
                    self._score(self._mask(self._view(kind, in_, player, holders)))
                ),
                self._index[player],
            ),
        )
        chosen: list[UUID] = []
        for player in ranked:
            if len(chosen) == wanted:
                break
            if all(self._fits(kind, player, other) for other in chosen) and (
                beside is None
                or self._stand_together(proposal, (*in_, *beside, *chosen, player))
            ):
                chosen.append(player)
        return tuple(chosen)

    def _new_versions(
        self,
        proposal: Proposal,
        may_be_dealt: Callable[..., bool],
        dealt: set[UUID],
        *,
        sizes: Callable[[int], Iterable[int]],
    ) -> None:
        """New versions of the game while there are fewer than three: each the
        evenest set of members who may be dealt it, with everybody In, of the
        first of ``sizes`` — given how many versions there are — that finds
        one."""

        kind = proposal.kind
        in_the_pool = tuple(p for p in proposal.yeses if p in self._members)
        refused = self._refused_by(proposal.posted_for)
        versions = len(proposal.versions)
        while versions < VERSIONS_PER_PROPOSAL:
            pool = self._mask(player for player in self._ids if may_be_dealt(player))
            people = next(
                (
                    found
                    for size in sizes(versions)
                    if (
                        found := self._evenest(
                            kind,
                            pool,
                            len(in_the_pool) + size,
                            must=in_the_pool,
                            refused=refused,
                        )
                    )
                    is not None
                ),
                None,
            )
            if people is None:
                return
            fits = people[len(in_the_pool) :]
            self._deal(proposal, fits, into=None)
            dealt.update(fits)
            versions += 1

    def versions_of_a_post(
        self,
        poster: UUID,
        kind: SearchMode,
        *,
        hour: CourtHourOnSale,
        posted_for: PostedFor,
    ) -> tuple[tuple[UUID, ...], ...]:
        pool = self._mask(
            player
            for player in self._ids
            if player != poster
            and self._may_play(
                player, kind, start=hour.start, share_grosze=hour.share_grosze
            )
            and self._admitted(posted_for, player)
        )
        refused = self._refused_by(posted_for)
        versions: list[tuple[UUID, ...]] = []
        while len(versions) < VERSIONS_PER_PROPOSAL:
            people = self._evenest(
                kind, pool, self._seats, must=(poster,), refused=refused
            )
            if people is None:
                break
            versions.append(people[1:])
            pool &= ~self._mask(people)
        if not versions:
            # Short of a full set: one version, its other seats open.
            for size in range(self._seats - 1, 1, -1):
                people = self._evenest(
                    kind, pool, size, must=(poster,), refused=refused
                )
                if people is not None:
                    versions.append(people[1:])
                    break
        return tuple(versions)

    def _holders(self, proposal: Proposal, named: Sequence[UUID]) -> list[UUID]:
        """Who of ``named`` still holds a seat on the game's version: not In,
        and not gone."""

        return [
            player
            for player in named
            if player not in proposal.yeses and not self._gone(proposal, player)
        ]

    def _admitted(self, posted_for: PostedFor | None, player: UUID) -> bool:
        member = self._members.get(player)
        return member is not None and admitted(posted_for, member)

    def _stand_together(self, proposal: Proposal, people: Iterable[UUID]) -> bool:
        return stand_together(
            proposal.who,
            self._genders,
            people,
            seats=self._seats,
        )

    def _refused_by(self, posted_for: PostedFor | None) -> Callable[[_Members], bool]:
        """A set of people who may not stand on one game the post is for — on
        *Mixed pairs*, more than two of a gender."""

        who = None if posted_for is None else posted_for.who
        if who is not Who.MIXED_PAIRS:
            return lambda people: False
        return lambda people: (
            not stand_together(
                who,
                self._genders,
                (self._ids[index] for index in _indices(people)),
                seats=self._seats,
            )
        )

    def _gone(self, proposal: Proposal, player: UUID) -> bool:
        """Whether a name on the game holds no seat on it any more: they said
        no, left the pool, or no longer fit somebody In."""

        return (
            player in proposal.declined
            or player not in self._members
            or not all(
                self._fits(proposal.kind, player, there) for there in proposal.yeses
            )
        )

    def _widens(self, proposal: Proposal) -> bool:
        """A pick at half its seats In with somebody named not yet swiped
        (the mechanics §6.3). A post is dealt its versions when it is posted."""

        return (
            proposal.origin is Origin.PICK
            and 2 * len(proposal.yeses) >= proposal.seats
            and any(
                player not in proposal.yeses
                and player not in proposal.declined
                and player not in proposal.withdrawn
                for player in named_on(proposal)
            )
        )

    def _deal(
        self, proposal: Proposal, players: tuple[UUID, ...], *, into: int | None
    ) -> None:
        self._deals.append(
            Deal(proposal_id=proposal.proposal_id, players=players, into=into)
        )
        self._dealt_at.setdefault(proposal.start, set()).update(players)
        self._hold(players)

    def _view(
        self,
        kind: SearchMode,
        in_: Sequence[UUID],
        player: UUID,
        holders: Sequence[UUID],
    ) -> tuple[UUID, ...]:
        """The card ``player`` would see: everybody In who is still a member,
        them, and the version's holders beside them in dealt order — the deck's
        own reading."""

        beside = [
            holder
            for holder in holders
            if holder != player and self._fits(kind, holder, player)
        ][: self._seats - len(in_) - 1]
        return (*(there for there in in_ if there in self._members), player, *beside)

    # ------------------------------------------------------------ who may play

    def _may_play(
        self, player: UUID, kind: SearchMode, *, start: Instant, share_grosze: int
    ) -> bool:
        """Whether this member may be dealt a game of ``kind`` from ``start``
        at ``share_grosze`` a seat."""

        member = self._members.get(player)
        return member is not None and may_play(
            member,
            kind,
            start=start,
            share_grosze=share_grosze,
            capped=self._capped[player],
        )

    def _fits(self, kind: SearchMode, one: UUID, other: UUID) -> bool:
        return frozenset((one, other)) not in self._unfit[kind]

    def _refusal(self, hour: CourtHourOnSale) -> Callable[[_Members], bool]:
        """What a set of people may not be dealt at ``hour``: a card with all of
        them on it already, and — at another club, for an official group — a
        game they could have had at home."""

        elsewhere = (
            hour.club_id != self._clubs.home_club_id
            and self._clubs.others_only_when_home_is_full
        )

        def refused(people: _Members) -> bool:
            return self._together(people) or (
                elsewhere and any(people & ~free == 0 for free in self._free_at_home)
            )

        return refused

    def _together(self, people: _Members) -> bool:
        """Whether these people are already on a card together, of either
        kind."""

        if people.bit_count() == self._seats:
            return people in self._full_games_on_cards
        return any(people & ~card == 0 for card in self._cards)

    def _picks_at(self, hour: CourtHourOnSale) -> int:
        """How many picks, of either kind, already hold the hour's courts."""

        return sum(
            1
            for proposal in self._live
            if proposal.origin is Origin.PICK
            # A request's court is off the hour's already: it holds it.
            and not proposal.waiting_for_the_club
            and (proposal.club_id, proposal.start) == (hour.club_id, hour.start)
        ) + sum(
            1
            for pick in self._picks
            if (pick.club_id, pick.start) == (hour.club_id, hour.start)
        )

    def _on_a_card_at(self, start: Instant) -> frozenset[UUID]:
        """Everybody on a card at this hour, of either kind — In or named."""

        return frozenset(
            {
                *(
                    player
                    for proposal in self._live
                    if proposal.start == start
                    for player in (*proposal.yeses, *named_on(proposal))
                ),
                *self._dealt_at.get(start, ()),
            }
        )

    # --------------------------------------------------------------- evenness

    def _evenest(
        self,
        kind: SearchMode,
        pool: _Members,
        size: int,
        *,
        must: tuple[UUID, ...] = (),
        refused: Callable[[_Members], bool] = lambda people: False,
    ) -> tuple[UUID, ...] | None:
        """The evenest ``size`` members holding ``must`` and drawn from
        ``pool``, every pair of them fit — ``must`` first, the rest in the
        pool's order — or ``None``. The first among equals, walked in the
        pool's order, so the answer is the same on every process
        (``docs/adr/0105``)."""

        must_mask = self._mask(must)
        pool = self._considered(pool & ~must_mask)
        for people in self._ranked_sets(kind, pool, size, must_mask):
            if not refused(people):
                rest = tuple(
                    self._ids[index] for index in _indices(people & ~must_mask)
                )
                return (*must, *rest)
        return None

    def _considered(self, pool: _Members) -> _Members:
        """The members of ``pool`` a game is chosen among: all of them, up to
        ``CONSIDERED_AT_AN_HOUR``, and past it those holding the fewest cards,
        the first to join first among equals."""

        members = list(_indices(pool))
        if len(members) <= CONSIDERED_AT_AN_HOUR:
            return pool
        members.sort(key=lambda index: self._holding[self._ids[index]])
        return sum(1 << index for index in members[:CONSIDERED_AT_AN_HOUR])

    def _ranked_sets(
        self, kind: SearchMode, pool: _Members, size: int, must: _Members
    ) -> list[_Members]:
        """Every set of ``size`` holding ``must`` and drawn from ``pool`` in
        which every pair fits, evenest first and in the walk's order among
        equals — once per distinct question in a batch. A clique walk, so a
        pair that does not fit prunes everything built on it."""

        key = (kind, pool, size, must)
        ranked = self._ranked.get(key)
        if ranked is not None:
            return ranked
        fitting = self._fitting[kind]
        need = size - must.bit_count()
        candidates = pool
        for index in _indices(must):
            candidates &= fitting[index]
        found: list[_Members] = []

        def extend(left: _Members, chosen: _Members, count: int) -> None:
            if count == need:
                found.append(chosen | must)
                return
            while left and left.bit_count() >= need - count:
                lowest = left & -left
                left ^= lowest
                extend(
                    left & fitting[lowest.bit_length() - 1], chosen | lowest, count + 1
                )

        if need >= 0:
            extend(candidates, 0, 0)
        # Stable, so equals keep the walk's order.
        found.sort(key=self._score, reverse=True)
        self._ranked[key] = found
        return found

    def _score(self, people: _Members) -> _Score:
        """The forecast of the evenest way these people could stand, then how
        close their Levels are."""

        cached = self._scores.get(people)
        if cached is not None:
            return cached
        levels = [self._levels[index] for index in _indices(people)]
        pct = 0
        if len(levels) > 1:
            pct = max(
                forecast(
                    yours,
                    theirs,
                    self._balance,
                    combine_group_sigma,
                    seats_per_side=self._per_side,
                ).pct
                for yours, theirs in _ways_to_stand(levels, self._per_side)
            )
        mus = [level.mu for level in levels]
        score = (pct, -(max(mus) - min(mus)))
        self._scores[people] = score
        return score

    def _mask(self, players: Iterable[UUID]) -> _Members:
        """These players as a set of members — anybody who is not one left out."""

        mask = 0
        for player in players:
            index = self._index.get(player)
            if index is not None:
                mask |= 1 << index
        return mask


def _indices(people: _Members) -> Iterator[int]:
    """The members in a set, in the pool's order."""

    while people:
        lowest = people & -people
        yield lowest.bit_length() - 1
        people ^= lowest


def _ways_to_stand(
    levels: Sequence[LevelReading], per_side: int
) -> Iterator[tuple[tuple[LevelReading, ...], tuple[LevelReading, ...]]]:
    """Every way two to four people could stand across the net, a side never
    over its seats and never empty — the deck's ``arrangements``, over Levels.
    The first person stands on the first side, so no way is read twice."""

    first, rest = levels[0], list(levels[1:])
    for partners in range(min(per_side - 1, len(rest)) + 1):
        for beside in combinations(range(len(rest)), partners):
            theirs = tuple(
                level for index, level in enumerate(rest) if index not in beside
            )
            if 1 <= len(theirs) <= per_side:
                yield (first, *(rest[index] for index in beside)), theirs


def _descending(score: _Score) -> tuple[int, float]:
    return (-score[0], -score[1])
