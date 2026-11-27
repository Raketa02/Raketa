"""Rescues as a reader is offered them — the rules that need no I/O (#545; the
mechanics §8.1–§8.2, §10.1, §14.2; the screens A2.3, A3.1, A4.3).

**A rescue is an open seat on a booked game**: somebody left, and the game is
still the others'. It is offered **until the club's cut-off, whatever the number
of open seats** — the leavers' refunds and the game itself depend on them being
taken — **then until the start**, on a game that goes ahead short; never on a
game called off, whether or not that is recorded yet. **A seat kept for a
rescuer whose share was refused** (#640) is offered to nobody else while their
time runs — read off the clock, so it is offered again the moment it is up.

**Offered to every member who fits and is free for the hour** (§10.1): the pair
rule against everybody on the game, through the kind's level window (the
matcher's own mask, as ``PlayerFit`` answers it); the kind their Play intent
wants — nothing until they have declared one, as the deck deals nothing; free
for the hour in their week; no game of theirs then; and within their **Games &
money**, as every card is. Never to somebody on the game, nor to a leaver of it:
a seat left is not offered back.

**The deck deals it only to the best fits** (§8.1): the offered members whose
game with them in the seat is best by **its kind's rule** (``domain/scoring.py``;
``docs/adr/0207`` §1, #831) — on a competitive game the one forecast most even,
on a For-fun game the best company for the people still on it: the vibe of
the three left and the candidate, then their new faces, then the forecast,
then the level spread — **three per open seat**, the number a no's seat is
dealt to (``NEXT_BEST_FITS_PER_SEAT``) — and the reader sits **on the side of
the seat that opened first**, the one their *I'm in* takes. Derived at every
read and stored nowhere, as the deck is.

**One borrow, pure**: ``free_for_the_hour`` from the Player profile's weekly
hours, the one rule the proposer, posting and the rescue board ask.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, exhaustive, instant, invariant
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.player_profile.domain.social_tags import SocialTag
from app.modules.player_profile.domain.weekly_hours import (
    WeeklyHours,
    free_for_the_hour,
)
from app.modules.proposals.domain.deck import (
    CardForecast,
    CardType,
    DeckCard,
    Sides,
    headline_of,
    hour_taken,
    week_of,
)
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.home import BookedGame, BookingStage, OpenSeat
from app.modules.proposals.domain.limits import NEXT_BEST_FITS_PER_SEAT, TIME_TO_PAY
from app.modules.proposals.domain.overlap import Overlap
from app.modules.proposals.domain.scoring import (
    Score,
    descending,
    new_faces_among,
    score_of,
    spread_of,
)
from app.modules.proposals.domain.vibe import social_vibe_share_of


@final
@dataclass(frozen=True, slots=True)
class Candidate:
    """What a rescue's offer reads of one member: the kinds they want, their
    week, the games they have booked, and their Games & money."""

    player_id: UUID
    #: Empty while they have declared no intent for the sport.
    wants: frozenset[SearchMode]
    week: WeeklyHours
    #: When each of their booked games starts, around the rescue's hour.
    booked: tuple[Instant, ...]
    limits: GamesAndMoney


def rescuable(game: BookedGame, *, now: Instant, by: UUID | None = None) -> bool:
    """Whether a seat on this booked game is there to take at ``now`` — **by**
    a player, a seat kept for another rescuer whose time runs is not (#640);
    with nobody named, whether any seat is open at all, kept or not."""

    kept = 0 if by is None else game.seats_kept(now=now, but=by)
    return (
        game.stage is BookingStage.SEAT_OPEN
        and len(game.open) > kept
        and game.called_off_reason(now) is None
        and now < game.start
    )


def kept_until(game: BookedGame, player: UUID, *, now: Instant) -> Instant | None:
    """Until when a seat is kept for this rescuer if their share is refused at
    ``now`` (#640) — **once**: refused again while it is kept, the time they
    had; ``None`` once theirs ran out, so a refusal pressed again and again
    holds no seat; otherwise ``TIME_TO_PAY`` on — to fix the card, never past
    the cut-off; after it, to pay — never past the start."""

    kept = game.kept_for(player, now=now)
    if kept is not None:
        return kept.until
    if player in game.kept:
        return None
    last = game.cut_off if fills_by_the_cut_off(game, now=now) else game.start
    return instant(min(now + TIME_TO_PAY, last))


def fills_by_the_cut_off(game: BookedGame, *, now: Instant) -> bool:
    """*fills by Fri 16:00* — before the cut-off, the game is off unless its
    seats are taken by then; after it, *offered until the start*."""

    return now < game.cut_off


def rescue_deadline(game: BookedGame, *, now: Instant) -> Instant:
    """When the seat leaves the board: the cut-off while it is ahead, then the
    start."""

    return game.cut_off if fills_by_the_cut_off(game, now=now) else game.start


def seat_to_take(game: BookedGame) -> OpenSeat:
    """The seat an *I'm in* takes: the one that opened first."""

    invariant(bool(game.open), f"{game.booking_id} has no seat open")
    return game.open[0]


def offered_to(
    game: BookedGame,
    candidate: Candidate,
    *,
    unfit: Collection[frozenset[UUID]],
    now: Instant,
    already_kept: bool = False,
) -> bool:
    """Whether this rescue is offered to this member at ``now``. ``unfit`` is
    every pair among them and the people on the game that may not share a
    court. ``already_kept`` for a seat kept for this rescuer while their time
    runs (#640): a claim made before, never asked the kind again (Q127)."""

    player = candidate.player_id
    if not rescuable(game, now=now, by=player):
        return False
    if player in game.players or player in game.leavers:
        return False
    if not already_kept and game.kind not in candidate.wants:
        return False
    if any(frozenset((player, other)) in unfit for other in game.players):
        return False
    if not free_for_the_hour(candidate.week, start=game.start, zone=CLUB_ZONE):
        return False
    if hour_taken(game.start, candidate.booked):
        return False
    if not candidate.limits.shows(share_grosze=game.share_grosze):
        return False
    week = week_of(game.start)
    booked_that_week = sum(1 for start in candidate.booked if week_of(start) == week)
    return booked_that_week < candidate.limits.games_per_week


def sides_for(game: BookedGame, reader: UUID) -> Sides:
    """The sides as the reader would stand, **in the seat that opened first**:
    its side theirs, with them first on it."""

    seat = seat_to_take(game)
    yours, theirs = (
        (game.first_side, game.second_side)
        if seat.side == "A"
        else (game.second_side, game.first_side)
    )
    return Sides(yours=(reader, *yours), theirs=theirs)


def best_fits(
    game: BookedGame,
    offered: Sequence[UUID],
    forecasts: Sequence[CardForecast | None],
    *,
    tags: Mapping[UUID, Collection[SocialTag]] | None = None,
    known: Collection[frozenset[UUID]] = (),
    levels: Mapping[UUID, float] | None = None,
) -> frozenset[UUID]:
    """The members the deck deals the seat to: of those offered — in the
    pool's order — the ones whose game with them in it is best by the game's
    kind's rule, **three per open seat**; the pool's order breaks a tie.

    **Competitive**: forecast most even, as ever — a forecast that could not
    be read ranks last. **For fun** (``docs/adr/0207`` §1): the table is the
    people still on the game and the candidate, scored by its Social vibe off
    ``tags``, then its new faces — every pair ``known`` doesn't name — then
    the forecast, an unread one under every read one, then the spread of its
    ``levels``, the Levels that can be read — all three required, an
    ``invariant``, once there is anybody to leave out."""

    invariant(len(offered) == len(forecasts), "a forecast per member offered")
    room = room_for_best_fits(game)
    if len(offered) <= room:
        # Nobody to leave out, whatever the rule would say.
        return frozenset(offered)
    match game.kind:
        case SearchMode.COMPETITIVE:
            ranked = sorted(
                range(len(offered)),
                key=lambda index: (_unevenness(forecasts[index]), index),
            )
        case SearchMode.FOR_FUN:
            invariant(
                tags is not None and levels is not None,
                f"{game.booking_id}'s For-fun best fits ranked without the company",
            )
            company = tags or {}
            mus = levels or {}

            def scored(index: int) -> Score:
                table = (*game.players, offered[index])
                read = forecasts[index]
                return score_of(
                    SearchMode.FOR_FUN,
                    vibe=social_vibe_share_of(table, company),
                    new_faces=new_faces_among(table, known),
                    forecast=_UNREAD if read is None else read.pct,
                    spread=spread_of(mus[one] for one in table if one in mus),
                )

            ranked = sorted(
                range(len(offered)),
                key=lambda index: (descending(scored(index)), index),
            )
        case _:
            exhaustive(game.kind)
    return frozenset(offered[index] for index in ranked[:room])


def room_for_best_fits(game: BookedGame) -> int:
    """How many best fits the seat is dealt to: three per open seat. Offered
    to no more than that, everybody offered is one, and nothing is ranked."""

    return NEXT_BEST_FITS_PER_SEAT * game.open_seats


#: A forecast that could not be read, under every one that could: a pct is at
#: least nought.
_UNREAD = -1


def _unevenness(forecast: CardForecast | None) -> int:
    # A forecast that could not be read after every one that could: a pct is
    # at most 100.
    return -forecast.pct if forecast is not None else 1


def card_of_a_rescue(
    game: BookedGame,
    *,
    sides: Sides,
    forecast: CardForecast | None,
    overlap: Overlap,
    now: Instant,
    tags: Mapping[UUID, Collection[SocialTag]],
) -> DeckCard:
    """The *Seat open* card: the players *paid*, the reader in the seat that
    opened first, the court, its name and its kind (#671), **Booked** — and
    the deadline the board says, the cut-off and then the start. A For-fun
    one says the vibe of the reader with the players still on it, from
    ``tags``, and no forecast (``docs/adr/0207`` §5): the seat is empty until
    somebody takes it, and the table is the people there."""

    shown, vibe = headline_of(
        game.kind,
        table=(*sides.yours, *sides.theirs),
        forecast=forecast,
        tags=tags,
    )
    return DeckCard(
        proposal_id=game.booking_id,
        type=CardType.SEAT_OPEN,
        kind=game.kind,
        challenger_id=None,
        club_id=game.club_id,
        start=game.start,
        share_grosze=game.share_grosze,
        deadline=rescue_deadline(game, now=now),
        in_=(),
        sides=sides,
        forecast=shown,
        vibe=vibe,
        overlap=overlap,
        open_seats_after_your_yes=game.open_seats - 1,
        version_count=1,
        no_free_cancellation=not fills_by_the_cut_off(game, now=now),
        court_name=game.court_name,
        indoor=game.indoor,
        # Held until the cut-off, taken at it (#637).
        paid=() if fills_by_the_cut_off(game, now=now) else game.players,
    )
