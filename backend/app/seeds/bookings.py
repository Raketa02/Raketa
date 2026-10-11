"""The protagonist's booked games, and her receipts (#541; the screens Part D).

**A booked game is a full card that filled** (``docs/adr/0029``): each is made
the way the dealer makes a pick — ``MakeProposal``, at an hour Bonarka Arena
sells padel — dealt to her and three of *Padel po pracy*'s crowd, and then said
yes to through ``SayYes``, the use case the phone's swipe runs, her yes last. So
the last yes **books** it: every seat held together through the run's own fake
provider — **taken at once** for the game on the day, which is after its
cut-off, and **held until the cut-off** for next week's (#637) — a Booking on
the first free court, the ordinary Game it opens and its chat, and a receipt
for each of the four whose share was taken. Nothing here opens a table.

**Two games, three states the screens draw**:

- **on the day** — the first hour still on sale today, which is after its
  cut-off as well; when none is left today, the first hour inside the club's
  cut-off instead, so a run late in the evening still seeds a game the club's
  free cancellation no longer covers;
- **before the cut-off** — the first hour on sale **next week**, so her own
  week holds one booked game and her *games per week* (two) leaves this week's
  cards in her deck.

**Out of the other layers' way**: neither hour is one of her answered picks'
hours, and each crowd member it seats is booked once — so neither *one game per
hour* nor anybody's *games per week* moves a yes the proposals layer seeded.

**And one game waiting for an On request club** (#543): Kazimierz Padel, a
kilometre from Bonarka and so one of the clubs her group plays at, is put a full
game of hers at the first padel hour it sells that holds none of her games — the
same ``MakeProposal`` and four ``SayYes``, the last answered *waiting for the
club*: nobody charged, the court held, the desk emailed. **It waits the club's
time to confirm** — an hour at Kazimierz — from the run's now, and then the
timeout job calls it off as unanswered; a re-run puts a fresh one.

**And one game of the crowd's filled far ahead** (#639): four of *Padel po
pracy*'s crowd — never her — fill Bonarka's first padel hour whose cut-off is
more than five days off. A card hold made without its player lasts 4 days 18
hours on a Visa, so each seat is **checked** at the fill — held for a moment and
let go — and held again at its **Holding time**, four days before the
cut-off, which the console's *hold the shares* runs. The four have no game that
week and no yes at the hour, so the fill moves nothing another layer seeded.

**Re-running books nothing twice**: an hour she already has a booked game at is
left as it is, a game of hers still waiting for Kazimierz is left waiting, a
far-ahead hour the crowd already booked is left as it is, and a later run on a
later day books later hours.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Final, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_booked_games,
    build_club_account_repository,
    build_club_terms,
    build_court_hours,
    build_domain_event_store,
    build_event_publisher,
    build_fake_payments,
    build_holding_times,
    build_make_proposal,
    build_player_bookings,
    build_pools,
    build_proposal_directory,
    build_read_receipts,
    build_say_yes,
    build_the_cut_off,
)
from app.core.config import Settings
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, hours, shifted
from app.modules.clubs.domain.court_hours import CLUB_ZONE, local_day
from app.modules.payments.domain.provider import PaymentProvider
from app.modules.proposals.application.answers import YesAnswer
from app.modules.proposals.application.commands import (
    AnswerProposalCommand,
    MakeProposalCommand,
)
from app.modules.payments.domain.seat_charge import HOLDING_LEAD
from app.modules.proposals.domain.deck import (
    DECK_HORIZON,
    GAME_LENGTH,
    week_of,
    week_window,
)
from app.modules.proposals.domain.home import BookingStage
from app.modules.proposals.domain.proposal import Origin
from app.modules.proposals.domain.proposer import CourtHourOnSale
from app.modules.users.domain.value_objects import Email
from app.seeds.clock import FixedClock
from app.seeds.clubs import SEED_CLUBS, SeedClub, desk_email
from app.seeds.proposals import (
    GAMES_CLUB,
    GAMES_KIND,
    GAMES_SPORT,
    SeededProposals,
    games_club_id,
    her_games_group,
)

#: The On request club her waiting game is put to — a kilometre from Bonarka,
#: so one of the clubs her group plays at.
WAITING_CLUB: Final = next(
    club for club in SEED_CLUBS if club.name == "Kazimierz Padel"
)

#: How far ahead of the run the far-ahead game's cut-off is, at least: past
#: the Holding time by a day, so a Visa's hold — 4 days 18 hours — cannot
#: reach it, and every seat is checked (#639).
FAR_AHEAD: Final = HOLDING_LEAD + timedelta(days=1)

#: The two states, in the order they are booked.
ON_THE_DAY: Final = "on the day"
AFTER_THE_CUT_OFF: Final = "after the cut-off"
BEFORE_THE_CUT_OFF: Final = "before the cut-off"


@final
@dataclass(frozen=True, slots=True)
class SeededBooking:
    state: str
    start: Instant
    #: Whether this run booked it, or found her booked then already.
    made: bool


@final
@dataclass(frozen=True, slots=True)
class SeededWaiting:
    """Her game waiting for an On request club."""

    start: Instant
    #: Whether this run put it to the club, or found it waiting already.
    made: bool


@final
@dataclass(frozen=True, slots=True)
class SeededFarAhead:
    """The crowd's game filled far ahead, its seats checked (#639)."""

    start: Instant
    #: The Holding time its checked seats are held at.
    hold_at: Instant | None
    #: How many of its four seats were checked.
    checked: int
    #: Whether this run booked it, or found it booked then already.
    made: bool


@final
@dataclass(frozen=True, slots=True)
class SeededBookings:
    bookings: tuple[SeededBooking, ...]
    #: Her receipts once the games were booked.
    receipts: int
    waiting: SeededWaiting | None = None
    far_ahead: SeededFarAhead | None = None

    @property
    def starts(self) -> tuple[Instant, ...]:
        """Every hour this layer booked or put to a club — what the layers
        after it keep out of the way of."""

        return (
            *(booking.start for booking in self.bookings),
            *([self.waiting.start] if self.waiting is not None else []),
            *([self.far_ahead.start] if self.far_ahead is not None else []),
        )


class NotEnoughToBook(RuntimeError):
    """The crowd, or what the club sells, cannot seat the games this layer
    promises."""


async def book_her_games(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
    seeded: SeededProposals,
) -> SeededBookings:
    """Book her two games and read her receipts. **After the proposals layer**,
    whose group, crowd and answered picks it reads and keeps out of the way of."""

    clock = FixedClock(at=now)
    # The run's own provider: every seeded card is one this fake answers as
    # ``A_CARD``, and the outbox the seed drains takes its holds.
    provider = build_fake_payments()
    async with session_factory() as session:
        found = await her_games_group(session)
        if found is None:
            raise NotEnoughToBook("the proposals layer has not gathered her group")
        her, group_id = found
        club_id = await games_club_id(session)
        hours_on_sale = await padel_hours_on_sale(session, club_id, now=now)
        targets = await _the_hours(session, club_id, hours_on_sale, seeded, now=now)
        partners = await _partners(session, group_id, her, seeded)
        booked = await build_booked_games(session).starts_of(
            her, start=now, end=now + DECK_HORIZON
        )

        bookings: list[SeededBooking] = []
        for index, (state, start) in enumerate(targets):
            if any(abs(start - game) < GAME_LENGTH for game in booked):
                bookings.append(SeededBooking(state, start, made=False))
                continue
            three = partners[3 * index : 3 * index + 3]
            if len(three) < 3:
                raise NotEnoughToBook(
                    f"{len(partners)} of the crowd cannot seat {len(targets)} "
                    f"booked games beside her"
                )
            await _book(
                session,
                settings=settings,
                clock=clock,
                provider=provider,
                pool_id=group_id,
                club_id=club_id,
                start=start,
                players=(*three, her),
            )
            bookings.append(SeededBooking(state, start, made=True))
        waiting = await _put_to_the_club(
            session,
            settings=settings,
            clock=clock,
            provider=provider,
            her=her,
            pool_id=group_id,
            partners=partners[3 * len(targets) : 3 * len(targets) + 3],
            seeded=seeded,
            now=now,
        )
        far_ahead = await _the_crowd_far_ahead(
            session,
            settings=settings,
            clock=clock,
            provider=provider,
            her=her,
            pool_id=group_id,
            club_id=club_id,
            on_sale=hours_on_sale,
            taken=[
                *(booking.start for booking in bookings),
                *(pick.start for pick in seeded.picks),
                waiting.start,
            ],
            now=now,
        )
        receipts = await build_read_receipts(session).execute(her)
    return SeededBookings(
        bookings=tuple(bookings),
        receipts=len(receipts),
        waiting=waiting,
        far_ahead=far_ahead,
    )


async def _the_crowd_far_ahead(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: FixedClock,
    provider: PaymentProvider,
    her: UUID,
    pool_id: UUID,
    club_id: UUID,
    on_sale: Sequence[CourtHourOnSale],
    taken: Sequence[Instant],
    now: Instant,
) -> SeededFarAhead:
    """Four of the crowd at Bonarka's first padel hour whose cut-off is more
    than ``FAR_AHEAD`` off — every seat checked at the fill (#639) — or the
    game an earlier run booked there."""

    terms = (await build_club_terms(session).of([club_id], now=now)).get(club_id)
    if terms is None:
        raise NotEnoughToBook(f"{GAMES_CLUB.name} sells nothing at {now}")
    notice = timedelta(hours=terms.cut_off_hours)
    start = next(
        (
            hour.start
            for hour in on_sale
            if hour.start - notice >= now + FAR_AHEAD
            and not any(abs(hour.start - other) < GAME_LENGTH for other in taken)
        ),
        None,
    )
    if start is None:
        raise NotEnoughToBook(
            f"{GAMES_CLUB.name} sells no padel hour whose cut-off is "
            f"{FAR_AHEAD.days} days past "
            f"{now.astimezone(CLUB_ZONE):%a %d %b %H:%M}"
        )
    pools = build_pools(session)
    pool = await pools.find(pool_id)
    crowd = [] if pool is None else await pools.members_of(pool)
    booked = build_booked_games(session)
    for member in crowd:
        if await booked.starts_of(member, start=start, end=start + GAME_LENGTH):
            # An earlier run's: the crowd booked this hour already.
            return await _far_ahead_as_it_is(
                session, start=start, players=(member,), made=False
            )
    four = await _four_free_at(session, crowd, her, start, now=now)
    answer = await all_say_yes(
        session,
        settings=settings,
        clock=clock,
        provider=provider,
        pool_id=pool_id,
        club_id=club_id,
        start=start,
        players=four,
    )
    if answer is None or answer.booked is None:
        raise NotEnoughToBook(
            f"the crowd's game at {start.astimezone(CLUB_ZONE):%a %d %b %H:%M} "
            f"filled and did not book: {answer!r}"
        )
    far = await _far_ahead_as_it_is(
        session,
        start=start,
        players=four,
        made=True,
        booking_id=answer.booked.booking_id,
    )
    if not far.checked:
        raise NotEnoughToBook(
            f"the crowd's game at {start.astimezone(CLUB_ZONE):%a %d %b %H:%M} "
            "booked far ahead with no seat checked"
        )
    return far


async def _far_ahead_as_it_is(
    session: AsyncSession,
    *,
    start: Instant,
    players: Sequence[UUID],
    made: bool,
    booking_id: UUID | None = None,
) -> SeededFarAhead:
    """How many of the far-ahead game's seats are checked, and when they are
    held — read off its seats' own Holding times."""

    if booking_id is None:
        return SeededFarAhead(start=start, hold_at=None, checked=0, made=made)
    times = build_holding_times(session)
    checked = [
        held
        for player in players
        for held in (await times.of(player, [booking_id])).values()
    ]
    return SeededFarAhead(
        start=start,
        hold_at=min(checked, default=None),
        checked=len(checked),
        made=made,
    )


async def _four_free_at(
    session: AsyncSession,
    crowd: Sequence[UUID],
    her: UUID,
    start: Instant,
    *,
    now: Instant,
) -> tuple[UUID, ...]:
    """Four of the crowd, in the order they joined, never her, with no game in
    the hour's week and no yes at the hour — so the fill moves nothing another
    layer seeded."""

    booked = build_booked_games(session)
    directory = build_proposal_directory(session)
    week_start, week_end = week_window([week_of(start)])
    four: list[UUID] = []
    for member in crowd:
        if member == her:
            continue
        if await booked.starts_of(member, start=week_start, end=week_end):
            continue
        yeses = await directory.live_yeses_of(member, now=now)
        if any(abs(yes.start - start) < GAME_LENGTH for yes in yeses):
            continue
        four.append(member)
        if len(four) == 4:
            return tuple(four)
    raise NotEnoughToBook(
        f"the crowd has no four free of games the week of "
        f"{start.astimezone(CLUB_ZONE):%a %d %b %H:%M} to fill a game far ahead"
    )


async def _put_to_the_club(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: FixedClock,
    provider: PaymentProvider,
    her: UUID,
    pool_id: UUID,
    partners: Sequence[UUID],
    seeded: SeededProposals,
    now: Instant,
) -> SeededWaiting:
    """Her full game at Kazimierz Padel, answered *waiting for the club* — or
    the one still waiting from an earlier run."""

    club_id = await club_id_of(session, WAITING_CLUB)
    hers = await build_player_bookings(session).of_player(her, since=None)
    already = next(
        (
            game
            for game in hers
            if game.stage is BookingStage.WAITING_FOR_THE_CLUB
            and game.club_id == club_id
        ),
        None,
    )
    if already is not None:
        return SeededWaiting(start=already.start, made=False)
    if len(partners) < 3:
        raise NotEnoughToBook(
            f"the crowd has no three left to wait for {WAITING_CLUB.name} with her"
        )
    taken = [game.start for game in hers] + [pick.start for pick in seeded.picks]
    start = next(
        (
            hour.start
            for hour in await padel_hours_on_sale(session, club_id, now=now)
            if not any(abs(hour.start - game) < GAME_LENGTH for game in taken)
        ),
        None,
    )
    if start is None:
        raise NotEnoughToBook(
            f"{WAITING_CLUB.name} sells no padel hour clear of her games from "
            f"{now.astimezone(CLUB_ZONE):%a %d %b %H:%M}"
        )
    answer = await all_say_yes(
        session,
        settings=settings,
        clock=clock,
        provider=provider,
        pool_id=pool_id,
        club_id=club_id,
        start=start,
        players=(*partners, her),
    )
    if answer is None or answer.waiting_until is None:
        raise NotEnoughToBook(
            f"her game at {WAITING_CLUB.name} on "
            f"{start.astimezone(CLUB_ZONE):%a %d %b %H:%M} did not go to the club: "
            f"{answer!r}"
        )
    return SeededWaiting(start=start, made=True)


async def club_id_of(session: AsyncSession, club: SeedClub) -> UUID:
    """The club its desk signed up, off the desk's account."""

    account = await build_club_account_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).get_by_email(Email(desk_email(club)))
    if account is None:
        raise RuntimeError(f"{club.name} has not signed up — the clubs run first")
    return account.club_id


async def padel_hours_on_sale(
    session: AsyncSession, club_id: UUID, *, now: Instant
) -> list[CourtHourOnSale]:
    on_sale = await build_court_hours(session).on_sale(
        [club_id], start=now, end=now + DECK_HORIZON, now=now
    )
    return sorted(
        (
            hour
            for hour in on_sale
            if hour.sport is GAMES_SPORT and hour.taking_new_cards
        ),
        key=lambda hour: hour.start,
    )


async def _the_hours(
    session: AsyncSession,
    club_id: UUID,
    on_sale: Sequence[CourtHourOnSale],
    seeded: SeededProposals,
    *,
    now: Instant,
) -> list[tuple[str, Instant]]:
    """The hour on the day — or inside the cut-off — and the first next week."""

    terms = (await build_club_terms(session).of([club_id], now=now)).get(club_id)
    if terms is None:
        raise NotEnoughToBook(f"{GAMES_CLUB.name} sells nothing at {now}")
    cut_off = shifted(now, hours(terms.cut_off_hours))
    today = next(
        (hour.start for hour in on_sale if local_day(hour.start) == local_day(now)),
        None,
    )
    soon = (
        (ON_THE_DAY, today)
        if today is not None
        else next(
            (
                (AFTER_THE_CUT_OFF, hour.start)
                for hour in on_sale
                if hour.start < cut_off
            ),
            None,
        )
    )
    picked = {pick.start for pick in seeded.picks}
    later = next(
        (
            hour.start
            for hour in on_sale
            if week_of(hour.start) > week_of(now) and hour.start not in picked
        ),
        None,
    )
    if soon is None or later is None:
        raise NotEnoughToBook(
            f"{GAMES_CLUB.name} sells no padel hour "
            f"{'inside its cut-off' if soon is None else 'next week'} from "
            f"{now.astimezone(CLUB_ZONE):%a %d %b %H:%M}"
        )
    return [soon, (BEFORE_THE_CUT_OFF, later)]


async def _partners(
    session: AsyncSession, group_id: UUID, her: UUID, seeded: SeededProposals
) -> list[UUID]:
    """The crowd, in the order they joined — first those named on none of her
    answered picks. A booked game is never at a pick's hour and one booking
    reaches nobody's *games per week*, so a yes seeded there stands either
    way; the order keeps the picks' people for her deck where it can."""

    pools = build_pools(session)
    pool = await pools.find(group_id)
    if pool is None:
        return []
    named = {player for pick in seeded.picks for player in pick.named}
    crowd = [member for member in await pools.members_of(pool) if member != her]
    return [
        *(member for member in crowd if member not in named),
        *(member for member in crowd if member in named),
    ]


async def _book(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: FixedClock,
    provider: PaymentProvider,
    pool_id: UUID,
    club_id: UUID,
    start: Instant,
    players: tuple[UUID, ...],
) -> None:
    answer = await all_say_yes(
        session,
        settings=settings,
        clock=clock,
        provider=provider,
        pool_id=pool_id,
        club_id=club_id,
        start=start,
        players=players,
    )
    if answer is None or answer.booked is None:
        raise NotEnoughToBook(
            f"her game at {start.astimezone(CLUB_ZONE):%a %d %b %H:%M} filled and "
            f"did not book: {answer!r}"
        )


async def all_say_yes(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: FixedClock,
    provider: PaymentProvider,
    pool_id: UUID,
    club_id: UUID,
    start: Instant,
    players: tuple[UUID, ...],
    sport: Sport = GAMES_SPORT,
    kind: SearchMode = GAMES_KIND,
) -> YesAnswer | None:
    """A pick at the hour for these players — four in padel — each saying yes
    in turn. The last one's answer."""

    proposal_id = await build_make_proposal(session, clock=clock).execute(
        MakeProposalCommand(
            pool_id=pool_id,
            origin=Origin.PICK,
            poster_id=None,
            sport=sport,
            kind=kind,
            club_id=club_id,
            start=start,
            versions=[list(players)],
        )
    )
    answer = None
    for player in players:
        answer = await build_say_yes(
            session, clock=clock, provider=provider, settings=settings
        ).execute(AnswerProposalCommand(proposal_id=proposal_id, player_id=player))
    return answer


async def the_cut_off_came(
    session: AsyncSession, *, settings: Settings, at: Instant
) -> None:
    """The cut-off job, run at ``at`` on a stopped clock — as the API's would
    have run it then (#637): every share held for a game whose cut-off has
    come by then is taken, and a game short at it called off. What a game
    filled before a cut-off that has passed since needs to read taken."""

    await build_the_cut_off(
        session, clock=FixedClock(at=at), settings=settings
    ).execute()


def booking_lines(seeded: SeededBookings) -> list[str]:
    """The report's section: her booked games, and her receipts."""

    lines = [
        f"Her booked games at {GAMES_CLUB.name}, four seats each — held until "
        "the cut-off, taken after it:"
    ]
    for booking in seeded.bookings:
        state = "booked" if booking.made else "already booked"
        money = "held" if booking.state == BEFORE_THE_CUT_OFF else "taken"
        lines.append(
            f"  {booking.start.astimezone(CLUB_ZONE):%a %d %b %H:%M} · "
            f"{booking.state} · {state} · {money}"
        )
    lines.append(f"  her receipts: {seeded.receipts}")
    if seeded.far_ahead is not None:
        far = seeded.far_ahead
        state = "booked" if far.made else "already booked"
        held = (
            ""
            if far.hold_at is None
            else f" · held from {far.hold_at.astimezone(CLUB_ZONE):%a %d %b %H:%M}"
        )
        lines.append(
            f"The crowd's game filled far ahead at {GAMES_CLUB.name}: "
            f"{far.start.astimezone(CLUB_ZONE):%a %d %b %H:%M} · {state} · "
            f"{far.checked} of 4 cards checked{held}"
        )
    if seeded.waiting is not None:
        state = "put to the club" if seeded.waiting.made else "still waiting"
        lines.append(
            f"Her game waiting for {WAITING_CLUB.name} (On request): "
            f"{seeded.waiting.start.astimezone(CLUB_ZONE):%a %d %b %H:%M} · {state}"
        )
    return lines
